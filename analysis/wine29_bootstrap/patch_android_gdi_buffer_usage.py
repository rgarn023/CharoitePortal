"""Request CPU-readable and CPU-writable buffers on WineAndroid's GDI lock path."""
from pathlib import Path
import sys

OLD = "        int ret = window->dequeueBuffer_DEPRECATED( window, &buffer );\n        if (!ret)\n        {\n            if ((ret = gralloc_lock( buffer, &buffer_ret->bits )))"
NEW = "        int ret = 0;\n\n        buffer_ret->bits = NULL;\n        /* The TextureView consumer needs GPU sampling, while GDI maps the\n         * producer buffer for CPU access. Request both before allocation. */\n        if (gralloc1_device || gralloc_module)\n            ret = window->perform( window, NATIVE_WINDOW_SET_USAGE,\n                                   GRALLOC_USAGE_HW_TEXTURE | GRALLOC_USAGE_SW_READ_OFTEN |\n                                   GRALLOC_USAGE_SW_WRITE_OFTEN );\n        if (!ret) ret = window->dequeueBuffer_DEPRECATED( window, &buffer );\n        if (!ret)\n        {\n            if ((ret = gralloc_lock( buffer, &buffer_ret->bits )))"


def patch_source(source):
    if source.count(OLD) != 1 or NEW in source:
        raise ValueError("Pinned WineAndroid GDI lock anchor mismatch")
    return source.replace(OLD, NEW)


if __name__ == "__main__":
    device = Path(sys.argv[1])
    device.write_text(patch_source(device.read_text(encoding="utf-8")), encoding="utf-8")
