/*

Grab images from the X11 display and send them to the SP108E LED controller.

Currently a proof-of-concept toy

TODO:
- SP103E related
    - Handle TCP segmentation better
    - Determine how to handle larger displays

- Rendering related
    - Allow switching on and off the serpentine LED layout
    - Allow arbitrary source-image to LED mappings
    - Map screen pixel colors to LED pixels RGB triplets
    - use XSHMGetImage for efficiency?

- need config options (commandline or config file)
    - hostname / port
    - Handle different size screengrabs
    - Allow different grab locations than 0,0
    - LED layout description

A good test is with a video file:

in one window:
    # for an 8x8 grab
    mplayer -geometry 16x16+-6+-24 video.mpg

    # for a 16x16 grab
    mplayer -geometry 26x23+-6+-24 video.mpg

in another window:
    ./x11-to-led

 */

#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/tcp.h>
#include <netdb.h>
#include <time.h>

#include <X11/Xlib.h>

int main(int argc, char **argv) {
    Display *d;

    if ((d = XOpenDisplay(NULL))==NULL) {
        printf("Could not open display\n");
        return 1;
    }

    struct hostent * he = gethostbyname("192.168.4.1");
    if (he == NULL) {
        perror("gethostbyname");
        return 1;
    }

    struct sockaddr_in sa;
    sa.sin_family = AF_INET;
    sa.sin_port = htons(8189);
    memcpy(&sa.sin_addr.s_addr,he->h_addr_list[0],he->h_length);
    
    int fd = socket(AF_INET, SOCK_STREAM, 6);
    if (fd == -1) {
        perror("socket");
        return 1;
    }

    int tmp=1;
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &tmp, sizeof(tmp));

    /* This is the bytes in an 8x8 pixel array */
    tmp=960;
    setsockopt(fd, IPPROTO_TCP, TCP_MAXSEG, &tmp, sizeof(tmp));

    if (connect(fd, (struct sockaddr *)&sa, sizeof(sa)) == -1) {
        perror("connect");
        return -1;
    }

    int s = DefaultScreen(d);

    /* CMD_CUSTOM_PREVIEW */
    send(fd, "\x38\x00\x00\x00\x24\x83", 6, 0);

    char buf[10];
    int size = recv(fd, buf, sizeof(buf), 0);
    /* TODO - confirm that we recv 0x31 */

    int grab_width = 16;
    int grab_height = 16;
    int pixels = grab_width*grab_height;
    char frame[900]; /* raw frame storage */
    int stride = sizeof(frame) / 3 / pixels * 3;

    time_t time_last = time(NULL);
    int frames = 0;

    while(1) {
        XImage * xi = XGetImage(
            d, RootWindow(d, s),
            0, 0, grab_width, grab_height,
            AllPlanes, ZPixmap
        );

/*
        printf("byte_order=%i bitmap_unit=%i bitmap_bit_order=%i bitmap_pad=%i\n",
            xi->byte_order, xi->bitmap_unit, xi->bitmap_bit_order,
            xi->bitmap_pad
        );
        printf("rmask=%x gmask=%x bmask=%x\n",
            xi->red_mask,
            xi->green_mask,
            xi->blue_mask
        );
*/

        memset(frame, 0, sizeof(frame));

        /* assume
            depth = 24, bits per pixel = 32, stride is bpp*width and RGB ordering
            (many of these assumptions are valid, the RGB ordering is not)
         */
        char *src = xi->data;
        char *dst = frame;
        int pix;

        for(int pairs = 0; pairs < grab_height/2; pairs++) {
            /* each pair has one Left to Right and one Right to Left row */

            /* R to L */
            src += (4*grab_width);
            char * saved_src = src;

            src --;
            for(int x=grab_width; x>0; x--) {
                /* TODO - this should not be hardcoded */
                src--; // 32 bits per pixel
                char red   = *src--;
                char green = *src--;
                char blue  = *src--;

                *(dst+0) = red;
                *(dst+1) = green;
                *(dst+2) = blue;
                dst+=stride;
            }
            src = saved_src;

            /* L to R */
            for(int x=0; x<grab_width; x++) {
                /* TODO - this should not be hardcoded */
                char blue  = *src++;
                char green = *src++;
                char red   = *src++;
                src++; // 32 bits per pixel

                *(dst+0) = red;
                *(dst+1) = green;
                *(dst+2) = blue;
                dst+=stride;
            }

        }

        send(fd, frame, sizeof(frame), 0);
        int size = recv(fd, buf, sizeof(buf), 0);
        /* TODO - confirm that we recv 0x31 */

        frames++;
        time_t time_now = time(NULL);
        if (time_now > time_last) {
            time_t deltat = time_now - time_last;
            printf("FPS: %i\n", frames / deltat);
            time_last = time_now;
            frames = 0;
        }
    }

    /* not reached */
    XCloseDisplay(d);
    return 0;
}
