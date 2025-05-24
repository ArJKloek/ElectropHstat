from electrophstat.gui.graph_controller import GraphController
from electrophstat.gui.plot_manager import PlotManager
from electrophstat.control.timer_control import monoTimer

def init_graphs(main):
    main.plot_manager = PlotManager(main)
    main.graph_ctrl = GraphController(main.tabWidget, main.plot_manager)
    main.logging_timer = monoTimer()
