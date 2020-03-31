#!/bin/sh

# Recursively archive and compress files from the current directory into
# ../boot/initramfs.gz
echo creating ../boot/initramfs.gz
find . | cpio -H newc -o | gzip -9 > ../boot/initramfs.gz
