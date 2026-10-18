/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdio.h>
#include <string.h>
#include <upnp.h>
#include <upnptools.h>

int main(void)
{
    char result[1024];
    const char *base = "http://127.0.0.1:12345/device.xml";
    int status = UpnpResolveURL(base, "item.xml", result);
    if (status != UPNP_E_SUCCESS ||
        strcmp(result, "http://127.0.0.1:12345/item.xml") != 0)
    {
        fprintf(stderr, "UPnP URL resolution failed: %d\n", status);
        return 1;
    }
    status = UpnpResolveURL("HTTP://127.0.0.1:12345/device.xml", "item.xml", result);
    if (status != UPNP_E_SUCCESS)
    {
        fprintf(stderr, "UPnP case-insensitive scheme failed: %d\n", status);
        return 1;
    }
    puts("UPnP matching HTTP schemes resolve normally; no network request made");
    return 0;
}
