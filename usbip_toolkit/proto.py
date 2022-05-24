from construct import *

# fmt: off

USBIP_VERSION_NUM = 0x0111

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

UBSIPCode = Enum(Int16ub,
    REQ_DEVINFO  = OP_REQ_DEVLIST,
    REP_DEVINFO  = OP_REP_DEVINFO,
    REQ_IMPORT   = OP_REQ_IMPORT,
    REP_IMPORT   = OP_REP_IMPORT,
    REQ_EXPORT   = OP_REQ_EXPORT,
    REP_EXPORT   = OP_REP_EXPORT,
    REQ_UNEXPORT = OP_REQ_UNEXPORT,
    REP_UNEXPORT = OP_REP_UNEXPORT,
    REQ_DEVLIST  = OP_REQ_DEVLIST,
    REP_DEVLIST  = OP_REP_DEVLIST
)

def Code(code):
    return Const(code, UBSIPCode)

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
    Padding(1)
)

OpCommon = Struct(
    USBIPVersion,
    "code" / Int16ub,
    "status" / Int32ub
)

OpDevInfoRequestBody = Struct(
    "busid" / BusID
)

OpDevInfoReply = Struct(
    *Hdr(UBSIPCode.REP_DEVINFO),
    "udev" / USBDevice,
    "uinf" / USBInterface[this.udev.bNumInterfaces]
)

OpImportRequestBody = Struct(
    "busid" / BusID
)

OpImportReply = Struct(
    *Hdr(UBSIPCode.REP_IMPORT),
    "udev" / USBDevice
)

OpExportRequestBody = Struct(
    "udev" / USBDevice
)

OpExportReply = Struct(
    *Hdr(UBSIPCode.REP_EXPORT),
    "returncode" / Int32ub
)

OpUnexportRequestBody = Struct(
    "udev" / USBDevice,
)

OpUnexportReply = Struct(
    *Hdr(UBSIPCode.REQ_UNEXPORT),
    "returncode" / Int32ub
)


OpDevListRequestBody = Struct()

OpDevListReplyExtra = Struct(
    "udev" / USBDevice,
    "uinf" / USBInterface[this.udev.bNumInterfaces]
)

OpDevListReply = Struct(
    *Hdr(UBSIPCode.REP_DEVLIST),
    "ndev" / Int32ub,
    "devs" / OpDevListReplyExtra[this.ndev]
)

OpRequest = Struct(
    USBIPVersion,
    "code" / UBSIPCode,
    "status" / Int32ub,
    "body" / Switch(this.code, {
        UBSIPCode.REQ_DEVINFO:  OpDevInfoRequestBody,
        UBSIPCode.REQ_IMPORT:   OpImportRequestBody,
        UBSIPCode.REQ_EXPORT:   OpExportRequestBody,
        UBSIPCode.REQ_UNEXPORT: OpUnexportRequestBody,
        UBSIPCode.REQ_DEVLIST:  OpDevListRequestBody,
    })
)

CMD_SUBMIT = 1
CMD_UNLINK = 2
RET_SUBMIT = 3
RET_UNLINK = 4


def CommonHdr(cmd):
    return (
        "command" / Const(cmd, Int32ub),
        "seqnum" / Int32ub,
        "devid" / Int32ub,
        "direction" / Int32ub,
        "ep" / Int32ub
    )

CmdSubmitHdr = Struct(
    *CommonHdr(CMD_SUBMIT),
    "transfer_flags" / Int32ub,
    "transfer_buffer_lenth" / Int32sb,
    "start_frame" / Const(0, Int32sb), # ISO not supported
    "number_of_packets" / Const(0, Int32sb), # ISO not supported
    "interval" / Int32sb,
    "setup" / Bytes(8),
    "transfer_buffer" / Bytes(this.transfer_buffer_length),
    # iso_packet_descriptor not used/supported
)

RetSubmitHdr = Struct(
    *CommonHdr(RET_SUBMIT),
    "status" / Int32sb,
    "actual_length" / Int32sb,
    "start_frame" / Const(0, Int32sb), # ISO not supported
    "number_of_packets" / Const(0, Int32sb), # ISO not supported
    "error_count" / Int32sb,
    Padding(8),
    "transfer_buffer" / Bytes(this.actual_length * this.direction),
    # iso_packet_descriptor not used/supported
)

CmdUnlinkHdr = Struct(
    *CommonHdr(CMD_UNLINK),
    "seqnum" / Int32ub,
    Padding(24)
)

RetUnlinkHdr = Struct(
    *CommonHdr(CMD_SUBMIT),
    "status" / Int32sb,
    Padding(24)
)

# fmt: on
