import socket

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

OpCommonHdrTuple = (
    USBIPVersion,
    "code" / UBSIPCode,
    USBIPStatus
)

OpCommonHdr = Struct(*OpCommonHdrTuple)

OpDevInfoRequestBody = Struct(
    "busid" / BusID
)

OpDevInfoRequest = Struct(
    *Hdr(UBSIPCode.REQ_DEVINFO),
    "body" / OpDevInfoRequestBody
)

OpDevInfoReplyBody = Struct(
    "udev" / USBDevice,
    "uinf" / USBInterface[this.udev.bNumInterfaces]
)

OpDevInfoReply = Struct(
    *Hdr(UBSIPCode.REP_DEVINFO),
    "body" / OpDevInfoReplyBody
)

OpImportRequestBody = Struct(
    "busid" / BusID
)

OpImportRequest = Struct(
    *Hdr(UBSIPCode.REQ_IMPORT),
    "body" / OpImportRequestBody
)

OpImportReplyBody = Struct(
    "udev" / USBDevice
)

OpImportReply = Struct(
    *Hdr(UBSIPCode.REP_IMPORT),
    "body" / OpImportReplyBody
)

OpExportRequestBody = Struct(
    "udev" / USBDevice
)

OpExportRequest = Struct(
    *Hdr(UBSIPCode.REQ_EXPORT),
    "body" / OpExportRequestBody
)

OpExportReplyBody = Struct(
    "returncode" / Int32ub
)

OpExportReply = Struct(
    *Hdr(UBSIPCode.REP_EXPORT),
    "body" / OpExportReplyBody
)

OpUnexportRequestBody = Struct(
    "udev" / USBDevice,
)

OpUnexportRequest = Struct(
    *Hdr(UBSIPCode.REQ_UNEXPORT),
    "body" / OpUnexportRequestBody,
)

OpUnexportReplyBody = Struct(
    "returncode" / Int32ub
)

OpUnexportReply = Struct(
    *Hdr(UBSIPCode.REP_UNEXPORT),
    "body" / OpUnexportReplyBody
)


OpDevListRequestBody = Struct()

OpDevListReplyExtra = Struct(
    "udev" / USBDevice,
    "uinf" / USBInterface[this.udev.bNumInterfaces]
)

OpDevListReplyBody = Struct(
    "ndev" / Int32ub,
    "devs" / OpDevListReplyExtra[this.ndev]
)

OpDevListReply = Struct(
    *Hdr(UBSIPCode.REP_DEVLIST),
    "body" / OpDevListReplyBody
)

OpRequest = Struct(
    *OpCommonHdrTuple,
    "body" / Switch(this.code, {
        UBSIPCode.REQ_DEVINFO:  OpDevInfoRequestBody,
        UBSIPCode.REQ_IMPORT:   OpImportRequestBody,
        UBSIPCode.REQ_EXPORT:   OpExportRequestBody,
        UBSIPCode.REQ_UNEXPORT: OpUnexportRequestBody,
        UBSIPCode.REQ_DEVLIST:  OpDevListRequestBody,
    })
)

OpReply = Struct(
    *OpCommonHdrTuple,
    "body" / Switch(this.code, {
        UBSIPCode.REP_DEVINFO:  OpDevInfoReplyBody,
        UBSIPCode.REP_IMPORT:   OpImportReplyBody,
        UBSIPCode.REP_EXPORT:   OpExportReplyBody,
        UBSIPCode.REP_UNEXPORT: OpUnexportReplyBody,
        UBSIPCode.REP_DEVLIST:  OpDevListReplyBody,
    })
)

UBSIPCommandEnum = Enum(Int32ub,
    CMD_SUBMIT = 1,
    CMD_UNLINK = 2,
    RET_SUBMIT = 3,
    RET_UNLINK = 4
)

def CommonHdr(cmd):
    return (
        "command" / Const(cmd, UBSIPCommandEnum),
        "seqnum" / Int32ub,
        "devid" / Int32ub,
        "direction" / Int32ub,
        "ep" / Int32ub
    )

CmdCommonHdrTuple = (
    "command" / UBSIPCommandEnum,
    "seqnum" / Int32ub,
    "devid" / Int32ub,
    "direction" / Int32ub,
    "ep" / Int32ub
)

CmdCommonHdr = Struct(*CmdCommonHdrTuple)

CmdSubmitBodyPrefixTuple = (
    "transfer_flags" / Int32ub,
    "transfer_buffer_length" / Int32sb,
    "start_frame" / Const(0, Int32sb), # ISO not supported
    "number_of_packets" / Const(0, Int32sb), # ISO not supported
    "interval" / Int32sb,
    "setup" / Bytes(8),
)

CmdSubmitBodyPrefix = Struct(*CmdSubmitBodyPrefixTuple)

CmdSubmitBody = Struct(
    *CmdSubmitBodyPrefixTuple,
    "transfer_buffer" / Bytes(this.transfer_buffer_length * (this._.direction ^ 1)),
    # iso_packet_descriptor not used/supported
)

CmdSubmit = Struct(
    *CommonHdr(UBSIPCommandEnum.CMD_SUBMIT),
    "body" / CmdSubmitBody
)

RetSubmitBody = Struct(
    "status" / Int32sb,
    "actual_length" / Int32sb,
    "start_frame" / Const(0, Int32sb), # ISO not supported
    "number_of_packets" / Const(0, Int32sb), # ISO not supported
    "error_count" / Int32sb,
    Padding(8),
    "transfer_buffer" / Bytes(this.actual_length * this._.direction),
    # iso_packet_descriptor not used/supported
)

RetSubmit = Struct(
    *CommonHdr(UBSIPCommandEnum.RET_SUBMIT),
    "body" / RetSubmitBody
)

CmdUnlinkBody = Struct(
    "seqnum" / Int32ub,
    Padding(24)
)

CmdUnlink = Struct(
    *CommonHdr(UBSIPCommandEnum.CMD_UNLINK),
    "body" / CmdUnlinkBody
)

RetUnlinkBody = Struct(
    "status" / Int32sb,
    Padding(24)
)

RetUnlink = Struct(
    *CommonHdr(UBSIPCommandEnum.CMD_SUBMIT),
    "body" / RetUnlinkBody
)

USBIPCommandRequest = Struct(
    *CmdCommonHdrTuple,
    "body" / Switch(this.command, {
        UBSIPCommandEnum.CMD_SUBMIT: CmdSubmitBody,
        UBSIPCommandEnum.CMD_UNLINK: CmdUnlinkBody,
    })
)

USBIPCommandReply = Struct(
    *CmdCommonHdrTuple,
    "body" / Switch(this.command, {
        UBSIPCommandEnum.RET_SUBMIT: RetSubmitBody,
        UBSIPCommandEnum.RET_UNLINK: RetUnlinkBody,
    })
)

# fmt: on


def read_usbip_packet(sock: socket.socket):
    buf = bytearray()
    first_2bytes = sock.read(2)
    if not first_2bytes:
        return None
    buf += first_2bytes
    if first_2bytes == USBIPVersion.build(None):
        # OpCommonHdr
        rest_op_cmn_hdr_buf = sock.read(OpCommonHdr.sizeof() - len(buf))
        if not rest_op_cmn_hdr_buf:
            return None
        buf += rest_op_cmn_hdr_buf
        cmn_hdr = OpCommonHdr.parse(buf)
        body_ty = {
            UBSIPCode.REQ_DEVINFO: OpDevInfoRequestBody,
            UBSIPCode.REQ_IMPORT: OpImportRequestBody,
            UBSIPCode.REQ_EXPORT: OpExportRequestBody,
            UBSIPCode.REQ_UNEXPORT: OpUnexportRequestBody,
            UBSIPCode.REQ_DEVLIST: OpDevListRequestBody,
        }[cmn_hdr.code]
        body_buf = sock.recv(body_ty.sizeof())
        if not body_buf:
            return None
        buf += body_buf
        res = OpRequest.parse(buf)
        rebuilt_sz = OpRequest.sizeof(**res)
    else:
        # USBIPCommand
        rest_cmd_cmn_hdr_buf = sock.recv(CmdCommonHdr.sizeof() - len(buf))
        if not rest_cmd_cmn_hdr_buf:
            return None
        buf += rest_cmd_cmn_hdr_buf
        cmn_hdr = CmdCommonHdr.parse(buf)
        body_ty = {
            UBSIPCommandEnum.CMD_SUBMIT: CmdSubmitBody,
            UBSIPCommandEnum.CMD_UNLINK: CmdUnlinkBody,
        }
        if body_ty is CmdSubmitBody:
            tbuf = sock.recv(8)
            if not tbuf:
                return None
            buf += tbuf
            transfer_len = int.from_bytes(tbuf[4:], "big")
            pkt_sz = CmdCommonHdr.sizeof() + CmdSubmitBodyPrefix.sizeof() + transfer_len
        else:
            pkt_sz = CmdCommonHdr.sizeof() + CmdUnlinkBody.sizeof()
        rest = sock.recv(pkt_sz - len(buf))
        if not rest:
            return None
        buf += rest
        res = USBIPCommandRequest.parse(buf)
        rebuilt_sz = USBIPCommandRequest.sizeof(**res)
    assert len(buf) == rebuilt_sz
    return res
