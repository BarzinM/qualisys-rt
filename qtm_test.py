import qtm as qtm





with qtm.QTMClient() as qt:
    qt.setup()
    qt.getAttitude()
    qt.getPacket()

