import configparser

def ConfigReader(self):
    config = configparser.ConfigParser()
    config.sections()
    config.read('settings.ini')
    ['settings.ini']
    config.sections()
    ['SETTINGS']
    interval =  config['SETTINGS']['Interval']
    pHSelect = config['SETTINGS']['pHSelect']
    ml = config['SETTINGS']['ml']
    reffile = config['SETTINGS']['reffile']
    addtime = config['SETTINGS']['addtime']
    select = config['SETTINGS']['select']
    cooldown = config['SETTINGS']['cooldown']
    lowpH = config['SETTINGS']['lowpH']
    midpH = config['SETTINGS']['midpH']
    highpH = config['SETTINGS']['highpH']



    self.log_interval = interval
    self.Ref_path = reffile
    self.pHSelect = pHSelect
    self.Select = select
    self.pHSelectMode = select
    self.ml = ml
    self.addtime = addtime
    self.pumpDurationSeconds = int(addtime)
    self.cooldown = cooldown
    self.lowpH = lowpH
    self.midpH = midpH
    self.highpH = highpH
    
    
def ConfigWriter(self):

    config = configparser.ConfigParser()
    config.read('settings.ini')
    configfile = open('settings.ini', 'w')
    config.set('SETTINGS','Interval', str(self.log_interval))
    config.set('SETTINGS','reffile', str(self.Ref_path))
    config.set('SETTINGS','pHSelect', str(self.pHSelect))
    config.set('SETTINGS','select', str(self.Select))
    config.set('SETTINGS','ml', str(self.ml))
    config.set('SETTINGS','addtime', str(self.addtime))
    config.set('SETTINGS', 'cooldown', str(self.cooldown))
    config.set('SETTINGS', 'lowpH', str(self.lowpH))
    config.set('SETTINGS', 'midpH', str(self.midpH))
    config.set('SETTINGS', 'highpH', str(self.highpH))
    
    config.write(configfile)
    configfile.close()
