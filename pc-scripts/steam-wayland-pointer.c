#define _POSIX_C_SOURCE 200809L

#include <X11/Xlib.h>
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>

#define IPC_COMMAND 0
#define IPC_MAGIC "i3-ipc"

static volatile sig_atomic_t running = 1;

static void stop_running(int signal_number) {
    (void)signal_number;
    running = 0;
}

static int write_all(int fd, const void *buffer, size_t length) {
    const char *cursor = buffer;
    while (length > 0) {
        ssize_t written = write(fd, cursor, length);
        if (written < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        cursor += written;
        length -= (size_t)written;
    }
    return 0;
}

static int read_all(int fd, void *buffer, size_t length) {
    char *cursor = buffer;
    while (length > 0) {
        ssize_t received = read(fd, cursor, length);
        if (received == 0) return -1;
        if (received < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        cursor += received;
        length -= (size_t)received;
    }
    return 0;
}

static int connect_sway(const char *path) {
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) return -1;

    struct sockaddr_un address = {0};
    address.sun_family = AF_UNIX;
    if (strlen(path) >= sizeof(address.sun_path)) {
        close(fd);
        errno = ENAMETOOLONG;
        return -1;
    }
    strcpy(address.sun_path, path);
    if (connect(fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        close(fd);
        return -1;
    }
    return fd;
}

static int sway_command(const char *socket_path, const char *command) {
    int fd = connect_sway(socket_path);
    if (fd < 0) return -1;

    uint32_t header[2] = {(uint32_t)strlen(command), IPC_COMMAND};
    if (write_all(fd, IPC_MAGIC, 6) < 0 ||
        write_all(fd, header, sizeof(header)) < 0 ||
        write_all(fd, command, header[0]) < 0) {
        close(fd);
        return -1;
    }

    char magic[6];
    uint32_t response_header[2];
    if (read_all(fd, magic, sizeof(magic)) < 0 ||
        memcmp(magic, IPC_MAGIC, sizeof(magic)) != 0 ||
        read_all(fd, response_header, sizeof(response_header)) < 0) {
        close(fd);
        return -1;
    }

    char response_buffer[512];
    uint32_t remaining = response_header[0];
    while (remaining > 0) {
        size_t chunk = remaining < sizeof(response_buffer)
            ? remaining : sizeof(response_buffer);
        if (read_all(fd, response_buffer, chunk) < 0) {
            close(fd);
            return -1;
        }
        remaining -= (uint32_t)chunk;
    }
    close(fd);
    return 0;
}

int main(void) {
    const char *sway_socket = getenv("SWAYSOCK");
    if (!sway_socket || !*sway_socket) {
        fprintf(stderr, "SWAYSOCK is not set; run this from your Sway session.\n");
        return 1;
    }

    Display *display = XOpenDisplay(NULL);
    if (!display) {
        fprintf(stderr, "Cannot connect to XWayland through DISPLAY.\n");
        return 1;
    }

    int test_fd = connect_sway(sway_socket);
    if (test_fd < 0) {
        fprintf(stderr, "Cannot connect to Sway IPC at %s: %s\n",
                sway_socket, strerror(errno));
        XCloseDisplay(display);
        return 1;
    }
    close(test_fd);

    signal(SIGINT, stop_running);
    signal(SIGTERM, stop_running);

    Window root = DefaultRootWindow(display);
    Window root_return, child_return;
    int root_x, root_y, window_x, window_y;
    int old_x = 0, old_y = 0;
    unsigned mask = 0;
    int initialized = 0;
    const struct timespec interval = {.tv_sec = 0, .tv_nsec = 8000000};

    fprintf(stderr, "Mirroring Steam/XWayland pointer input into Sway.\n");

    while (running) {
        if (!XQueryPointer(display, root, &root_return, &child_return,
                           &root_x, &root_y, &window_x, &window_y, &mask)) {
            nanosleep(&interval, NULL);
            continue;
        }

        if (!initialized || root_x != old_x || root_y != old_y) {
            char command[96];
            /* Sway treats zero as "do not update this axis". */
            int sway_x = root_x == 0 ? 1 : root_x;
            int sway_y = root_y == 0 ? 1 : root_y;
            snprintf(command, sizeof(command),
                     "seat seat0 cursor set %d %d", sway_x, sway_y);
            if (sway_command(sway_socket, command) < 0) break;
        }

        initialized = 1;
        old_x = root_x;
        old_y = root_y;
        nanosleep(&interval, NULL);
    }

    XCloseDisplay(display);
    return running ? 1 : 0;
}
