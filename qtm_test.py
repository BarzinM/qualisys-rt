import qtm as qtm


with qtm.QTMClient() as qt:
    qt.setup()
    qt.getAttitude()
    print qt.getBody(0)['linear_x']
