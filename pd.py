import sigrokdecode as srd

class States:
    IDLE, GET_SLAVE_ADDR, READ_REGISTER, WRITE_REGISTER, GET_OFFSET, OFFSET_RECEIVED, READ_REGISTER_WOFFSET, WRITE_REGISTER_WOFFSET = range(8)

class Annotations:
    address, register, fields, debug = range(4)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ddc'
    name = 'DDC'
    longname = 'DISPLAY DATA CHANNEL'
    desc = """DISPLAY DATA CHANNEL:
    SCDC: Status and Control Data Channel for HDMI2.0
    EDID: 
    HDCP:"""
    license = 'gplv2+'
    inputs = ['i2c']
    outputs = ['ddc']
    annotations = ( ('Address', 'I²C address'),
                    ('Register', 'Register name and offset'),
                    ('Fields', 'Readable register interpretation'),
                    ('Debug', 'Debug messages'))
    annotation_rows = ( ('ddc', 'DDC', (0,1,2)),
                        ('debug', 'Debug', (3,)))

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = States.IDLE # I2C channel state
        self.reg = None     # actual register address
        self.offset = None  # offset is used in SCDC and HDCP register reads 
        self.protocol = None # 'scdc' or 'hdcp'
        self.databytes = [] # databytes

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def handle_scdc(self, addr, read_notwrite, data):
        pass
    
    def handle_EDID(self, data):
        pass

    def handle_HDCP(self, addr, read_notwrite, data):
        pass


    def decode(self, ss, es, data):
        cmd, databyte = data
        # store start and end samples
        self.ss = ss
        self.es = es

        self.put(self.ss, self.es, self.out_ann, [Annotations.debug, [str(self.state) + ' ' + cmd]])
        # State machine.
        if self.state == States.IDLE:
            # Wait for an I²C START condition.
            if cmd != 'START':
                return
            
            self.state = States.GET_SLAVE_ADDR 
        elif cmd in ('ACK', 'NACK'):
            return           
        elif self.state == States.GET_SLAVE_ADDR:
            # Wait for an address read/write operation.
            if cmd in ('ADDRESS READ', 'ADDRESS WRITE'):
                # If address write is 0xA8 then SCDC and next byte is the offset
                if cmd == 'ADDRESS WRITE' and databyte == 0xA8:
                    self.protocol = 'scdc'
                    self.state = States.GET_OFFSET
                # if address write is 0x74 then HDCP and next byte is the offset
                elif cmd == 'ADDRESS WRITE' and databyte == 0x74:
                    self.protocol = 'hdcp'
                    self.state = States.GET_OFFSET
                # if address read is 0x75 then it is a HDCP reg read
                elif cmd == 'ADDRESS READ' and databyte == 0x75:
                    self.protocol = 'hdcp'
                    self.state = States.READ_REGISTER
                # if address read is 0xA9
                elif cmd == 'ADDRESS READ' and databyte == 0xA9:
                    self.protocol = 'scdc'
                    self.state = States.READ_REGISTER
                # else:
                #     self.state = cmd[8:] + ' REGS' # READ REGS / WRITE REGS

        elif self.state == States.GET_OFFSET:
            if cmd == 'DATA WRITE':
                # get offset after this either:
                self.offset = databyte
                self.put(self.ss, self.es, self.out_ann, [2, ['Offset: {:2x}'.format(databyte)]])
                self.state = States.OFFSET_RECEIVED

        elif self.state == States.OFFSET_RECEIVED:
            # - START REPEAT comes - register read
            if cmd == 'START REPEAT':
                self.state = States.GET_SLAVE_ADDR
            # - another data byte - register write
            elif cmd == 'DATA WRITE':
                self.databytes.append(databyte)
                self.state = States.WRITE_REGISTER                

        elif self.state in (States.READ_REGISTER, States.WRITE_REGISTER):
            if cmd in ('DATA READ', 'DATA WRITE'):
                self.databytes.append(databyte)

            elif cmd == 'STOP':
                # TODO: Any output?
                self.reset()
                self.state = States.IDLE

