/*

Grab images from the X11 display and send them to the SP108E LED controller.

Currently a proof-of-concept toy

TODO:
- SP103E related
    - Handle TCP segmentation better
    - Determine how to handle larger displays
    - Understand why there are 15 bytes per pixel - can we compress the data?

- Rendering related
    - Handle serpentine LED layout
    - Allow arbitrary source-image to LED mappings
    - Map screen pixel colors to LED pixels RGB triplets

- need config options (commandline or config file)
    - hostname / port
    - Handle different size screengrabs
    - Allow different grab locations than 0,0
    - LED layout description

A good test is with a video file:

in one window:
    mplayer -geometry 16x16+-6+-24 video.mpg

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

    int grab_width = 8;
    int grab_height = 8;
    char frame[grab_height*grab_width*15]; /* raw frame storage */

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

        for(pix=0; pix<60; pix++) {
            *dst++ = *src++;
            *dst++ = *src++;
            *dst++ = *src++;
            src++;
            dst+=12;
        }

        send(fd, frame, sizeof(frame), 0);
        int size = recv(fd, buf, sizeof(buf), 0);
        /* TODO - confirm that we recv 0x31 */

    }

    /* not reached */
    XCloseDisplay(d);
    return 0;
}
