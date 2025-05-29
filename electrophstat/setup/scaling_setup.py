from PyQt5.QtCore import QSize


def apply_scaling(self):
    # Get current window size
    width = self.width()
    height = self.height()

    # Base scaling factor
    scale = min(width / 960, height / 600)
    font_size = (18 * scale)
        
    border_size = (2 *scale)
        
    start_padding = int(12 * scale)
    stop_padding = int(10 * scale)
    reset_padding = int(8 * scale)
        
    start_width = int(120 * scale)
    stop_width = int(100 * scale)
    reset_width = int(90 * scale)

    start_height = int(70 * scale)
    stop_height = int(55 * scale)
    reset_height = int(40 * scale)
        
        
    label_size = int(13 * scale)
    tick_size = int(11 * scale)

    for plot in self.graphWidgets:
        self.plot_manager._scale_graph_fonts(plot, label_size, tick_size)

        
    dial_size = int(70 * scale)
    self.voltageDial.setFixedSize(dial_size, dial_size)
    self.currentDial.setFixedSize(dial_size, dial_size)
        
     
    powerButton_width = int(60 * scale)
    powerButton_height = int(40 * scale)
    self.powerButton.setFixedSize(powerButton_width, powerButton_height)
    modeButton_width = int(40 * scale)
    modeButton_height = int(60 * scale)
    self.modeToggle.setFixedSize(modeButton_width, modeButton_height)
        

    usb_button_size = int(60 * scale)
    usb_button_icon = int(55 * scale)
    self.usb_button.setMinimumSize(usb_button_size, usb_button_size)
    self.usb_button.setIconSize(QSize(usb_button_icon, usb_button_icon))
        
    button_size = int(60 * scale)  # scale from window size
        
    self.setButton.setFixedSize(button_size, button_size)


    def set_font(widget, base_size):
        if widget is not None:
            font = widget.font()
            font.setPointSizeF(base_size * scale)
            widget.setFont(font)
        
    set_font(self.pHLabel, 25)
    set_font(self.RTDLabel, 18)
    set_font(self.lb_turbidity, 18)
    set_font(self.phSpin, 10)
    set_font(self.keepSelector, 10)
    set_font(self.voltagelabel, 14)
    set_font(self.currentlabel, 14)
    set_font(self.modelabel, 14)
    #set_font(self.voltageDiallabel, 10)
    # Update Start button stylesheet with dynamic font size
    start_style = f"""
        QPushButton {{
            background-color: #52BE80;
            font-size: {font_size}pt;
            font-weight: bold;
            padding: {start_padding}px;
            min-width: {start_width}px;
            min-height: {start_height}px;
            border: {border_size}px solid #229954;  
            border-radius: 12px; 
        }}
        QPushButton:pressed {{
            background-color: #229954;
            border: {border_size}px solid #1A7F42;

        }}
        QPushButton:disabled {{
            background-color: #D4EFDF;
            border: {border_size}px solid #A9DFBF;

        }}
    """
    stop_style = f"""
        QPushButton {{
            background-color: #C0392B;
            color: white;
            font-size: {font_size}pt;
            font-weight: bold;
            padding: {stop_padding}px;
            min-width: {stop_width}px;
            min-height: {stop_height}px;
            border: {border_size}px solid #922B21;
            border-radius: 12px; 

        }}
        QPushButton:pressed {{
            background-color: #922B21;
            border: {border_size}px solid #641E16;
        }}
        QPushButton:disabled {{
            color: lightGray;
            background-color: #FDEDEC;
            border: {border_size}px solid #FADBD8;
        }}
    """
    reset_style = f"""
        QPushButton {{
            background-color: #F1C40F;
            color: black;
            font-size: {font_size}pt;
            font-weight: bold;
            padding: {reset_padding}px;
            min-width: {reset_width}px;
            min-height: {reset_height}px;
            border: {border_size}px solid #B7950B; 
            border-radius: 12px; 

        }}
        QPushButton:pressed {{
            background-color: #B7950B;
            border: {border_size}px solid #9A7D0A;

        }}
        QPushButton:disabled {{
            color: lightGray;
            background-color: #FEF9E7;
            border: {border_size}px solid #FCF3CF;

        }}
    """

    self.startbutton.setStyleSheet(start_style)
    self.stopbutton.setStyleSheet(stop_style)
    self.resetbutton.setStyleSheet(reset_style)
    
    tab_font_size = int(10 * scale)
    tab_height = int(20 * scale)
    tab_width = int(110 * scale)
    tab_padding = int(5 * scale)

    tab_style = f"""
        QTabBar::tab {{
            font-size: {tab_font_size}pt;
            height: {tab_height}px;
            width: {tab_width}px;
            padding: {tab_padding}px;
        }}
    """
    self.tabWidget.setStyleSheet(tab_style)