from construct import *

# fmt: off

USBIP_VERSION_NUM = 1

SYSFS_PATH_MAX    = 256
SYSFS_BUS_ID_SIZE = 32

OP_REQUEST        = (0x80 << 8)
OP_REPLY          = (0x00 << 8)

OP_DEVINFO        = 0x02
OP_REQ_DEVINFO    = (OP_REQUEST | OP_DEVINFO)
OP_REP_DEVINFO    = (OP_REPLY   | OP_DEVINFO)

OP_IMPORT         = 0x03
OP_REQ_IMPORT     = (OP_REQUEST | OP_IMPORT)
OP_REP_IMPORT     = (OP_REPLY   | OP_IMPORT)

OP_EXPORT         = 0x06
OP_REQ_EXPORT     = (OP_REQUEST | OP_EXPORT)
OP_REP_EXPORT     = (OP_REPLY   | OP_EXPORT)

OP_UNEXPORT       = 0x07
OP_REQ_UNEXPORT   = (OP_REQUEST | OP_UNEXPORT)
OP_REP_UNEXPORT   = (OP_REPLY   | OP_UNEXPORT)

OP_DEVLIST        = 0x05
OP_REQ_DEVLIST    = (OP_REQUEST | OP_DEVLIST)
OP_REP_DEVLIST    = (OP_REPLY   | OP_DEVLIST)

BusID             = PaddedString(SYSFS_BUS_ID_SIZE, "utf8")
USBIPVersion      = "version" / Const(USBIP_VERSION_NUM, Int16ub)
USBIPStatus       = "status" / Int32ub

def Code(code):
    return Const(code, Int16ub)

def Hdr(code):
    return (
        USBIPVersion,
        Code(code),
        USBIPStatus
    )

USBDevice = Struct(
    "path" / PaddedString(SYSFS_PATH_MAX, "utf8"),
    "busid" / BusID,
    "busnum" / Int32ub,
    "devnum" / Int32ub,
    "speed" / Int32ub,
    "idVendor" / Int16ub,
    "idProduct" / Int16ub,
    "bcdDevice" / Int16ub,
    "bDeviceClass" / Int8ub,
    "bDeviceSubClass" / Int8ub,
    "bDeviceProtocol" / Int8ub,
    "bConfigurationValue" / Int8ub,
    "bNumConfigurations" / Int8ub,
    "bNumInterfaces" / Int8ub
)

USBInterface = Struct(
    "bInterfaceClass" / Int8ub,
    "bInterfaceSubclass" / Int8ub,
    "bInterfaceProtocol" / Int8ub,
    Padding(8)
)

OpCommon = Struct(
    USBIPVersion,
    "code" / Int16ub,
    "status" / Int32ub
)

OpDevInfoRequest = Struct(
    *Hdr(OP_REQ_DEVINFO),
    "busid" / BusID
)

OpDevInfoReply = Struct(
    *Hdr(OP_REP_DEVINFO),
    "udev" / USBDevice,
    "uinf" / USBInterface[this.udev.bNumInterfaces]
)

OpImportRequest = Struct(
    *Hdr(OP_REQ_IMPORT),
    "busid" / BusID
)

OpImportReply = Struct(
    *Hdr(OP_REP_IMPORT),
    "udev" / USBDevice
)

OpExportRequest = Struct(
    *Hdr(OP_REQ_EXPORT),
    "udev" / USBDevice
)

OpExportReply = Struct(
    *Hdr(OP_REP_EXPORT),
    "returncode" / Int32ub
)

OpUnexportRequest = Struct(
    *Hdr(OP_REQ_UNEXPORT),
    "udev" / USBDevice
)

OpUnexportReply = Struct(
    *Hdr(OP_REQ_UNEXPORT),
    "returncode" / Int32ub
)

OpDevListRequest = Struct(
    *Hdr(OP_REQ_DEVLIST),
)

OpDevListReplyExtra = Struct(
    "udev" / USBDevice,
    "uinf" / USBInterface[this.udev.bNumInterfaces]
)

OpDevListReply = Struct(
    *Hdr(OP_REP_DEVLIST),
    "ndev" / Int32ub,
    "devs" / OpDevListReplyExtra[this.ndev]
)

# fmt: on
