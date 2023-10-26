import logging
import PySimpleGUI as sg
import threading
import time
from amcc.instruments.ice_oxford_dryice import IceOxfordDryIce

# Taken extensively from https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Multithreaded_Long_Tasks.py

def ice_gui(ice):

    button_config1 = dict(
        size = (15, 2),
        font = ('arial', 15),
        )
        
    button_config2 = dict(
        size = (25, 1),
        font = ('arial', 10),
        )

    button_config3 = dict(
        size = (20, 1),
        font = ('arial', 10),
        )
    
    button_connect = sg.Button('Connect',
                            **button_config3,
                            tooltip=
"""Connects to ICE Remote Comms Service""")

    button_disconnect = sg.Button('Disconnect',
                            **button_config3,
                            tooltip=
"""None""")
    
    button_init = sg.Button('Initialize system parameters',
                            **button_config1,
                            tooltip=
"""Initializes all parameters to sane values.
Use after restarting main ICE software""")

    button_cancel = sg.Button('Cancel current command',
                              button_color = 'red',
                            **button_config1,
                            tooltip=
"""Cancels any ongoing processes""")

    button_change_sample = sg.Button('Change sample',
                            **button_config1,
                            tooltip=
"""Vents the sample space with helium, then """)
    
    button_cooldown = sg.Button('Cooldown',
                            **button_config1,
                            tooltip=
"""Begins cooldown process. Begins by cooling down using
 both the VTI and dynamic needle valves. When it reaches 
target temperature, switches over to "static" mode that
only cools the VTI""")
    
    button_hibernate = sg.Button('Hibernate',
                            **button_config1,
                            tooltip=
"""Puts the system into a resting state after
you are done with your experiment and ready to walk away""")


    button_load_and_cooldown = sg.Button('Load and cooldown',
                            **button_config1)    


    button_unload_and_hibernate = sg.Button('Unload and hibernate',
                            **button_config1)

    button_pump_sample_space = sg.Button('Pump sample space',
                            **button_config2,
                            tooltip=
""" Fixme """)
    
    button_purge = sg.Button('Purge gas and sample space',
                            **button_config2,
                            tooltip=
""" Fixme """)
    
    button_boil = sg.Button('Boil off liquid helium',
                            **button_config2,
                            tooltip=
""" Fixme """)
    
    button_precool = sg.Button('Precool VTI',
                            **button_config2,
                            tooltip=
""" Fixme """)
    
    button_exchange_gas = sg.Button('Add exchange gas',
                            **button_config2,
                            tooltip=
""" Fixme """)

    button_exit = sg.Button('Exit',
                            **button_config2,
                            tooltip=
""" Fixme """)
    
    buttons = [button_connect, button_disconnect, button_init, button_cancel, button_change_sample, button_cooldown, button_hibernate, button_pump_sample_space, button_purge, button_boil, button_precool, button_exchange_gas, button_exit]
    
    layout = [  #[],
            [sg.Text('User initials:'), sg.Input(key='user-initials', font = ('arial', 12), size = (8,1))],             # input field where you'll type command
            [sg.Text('Basic commands', font = ('arial', 15))],
            [button_init, button_change_sample],
            [button_cooldown, button_hibernate],
            [button_load_and_cooldown, button_unload_and_hibernate],
            [sg.Text('Advanced commands', font = ('arial', 15))],
            [button_pump_sample_space, button_purge],
            [button_boil, button_precool],
            [button_exchange_gas],
            [sg.Output(size=(80,15), key='log')],          # an output area where all print output will go
            [button_connect, button_disconnect],
            [button_exit] ]     # a couple of buttons

    window = sg.Window('ICE Oxford DRY ICE 1.5K Interface', layout, element_justification='c', finalize=True)
    
    
    # Create a new logging handler so that 
    class Handler(logging.StreamHandler):
        # From https://github.com/PySimpleGUI/PySimpleGUI/issues/2968
        # To allow the python logging to show up in the Output pane of the GUI
    
        def __init__(self):
            logging.StreamHandler.__init__(self)
    
        def emit(self, record):
            window['log'].write(f'{record.asctime} - {record.message}\n')
    
    new_handler = Handler()
    new_handler.setLevel(logging.INFO)
    ice.logger.logger.addHandler(new_handler)
    
    def erase_update_lines(window):
        """ Removes any lines that end in '*' so that updates (e.g. about 
        pressure or temperature) don't spam the GUI log """
        log = window['log'].get()
        lines = log.splitlines()
        lines_to_delete = [n for n, line in enumerate(lines) if line[-1] == '*']
        if len(lines_to_delete) >= 1: lines_to_delete = lines_to_delete[:-1]
        new_lines =  [line for n, line in enumerate(lines) if n not in lines_to_delete]
        window['log'].update("\n".join(new_lines) + '\n')

    def run_command_in_thread(cmd, args, finish_statement):
        # Define a new wrapper function to execute `cmd` then print a finish statement
        def newcmd(*args):
            cmd(*args)
            ice.logger.info(finish_statement)
            
        task = threading.Thread(target=newcmd, args=args, daemon=True)
        task.start()
        return task
        
    # Begin by executing Connect command
    event = 'Connect'
    user_initials = ''
    task = None
    while True:
        try:
            if event == 'Connect':
                ice.logger.info('--- Connecting ---')
                ice.ice_connect()
                ice.logger.info('--- Done connecting ---')
            elif event == 'Disconnect':
                ice.logger.info('--- Disconnecting ---')
                ice.ice_disconnect()
                ice.logger.info('--- Done disconnecting ---')
            elif event == 'Initialize system parameters':
                ice.logger.info('--- Initializing system parameters ---')
                task = run_command_in_thread(ice.initialize_system_parameters, (), '--- Done initializing system parameters ---')
            elif event == 'Change sample':
                ice.logger.info('--- Changing sample ---')
                task = run_command_in_thread(ice.change_sample, (), '--- Done changing sample ---')
            elif event == 'Cooldown':
                ice.logger.info('--- Cooling down ---')
                # task = run_command_in_thread(ice.c, (), '--- Done cooling down ---')
            elif event == 'Hibernate':
                ice.logger.info('--- Hibernating / putting system into resting state ---')
                task = run_command_in_thread(ice.hibernate, (), '--- Done hibernating, system in resting state ---')
                window['user-initials'].update('')
            # elif event == 'Unload and hibernate':
            #     ice.logger.info('--- Unloading then hibernating (put system into resting state) ---')
            #     task = run_command_in_thread(ice.change_sample, (), '--- Done changing sample ---')
            #     task = run_command_in_thread(ice.hibernate, (), '--- Done hibernating, system in resting state ---')
            #     window['user-initials'].update('')
            elif event == 'Add exchange gas':
                ice.logger.info('--- Adding exchange gas ---')
                task = run_command_in_thread(ice.add_exchange_gas, (10,), '--- Done adding exchange gas ---')
            elif event == 'Precool VTI':
                ice.logger.info('--- Precooling VTI ---')
                task = run_command_in_thread(ice.precool_vti, (), '--- Done precooling VTI ---')
            elif event == 'Boil off liquid helium':
                ice.logger.info('--- Boiling off any excess liquid helium in VTI/dynamic ---')
                task = run_command_in_thread(ice.boil_off_liquid_helium, (), '--- Done boiling off any excess liquid helium in VTI/dynamic ---')
            elif event == 'Purge gas and sample space':
                ice.logger.info('--- Purging gas box and sample space  with helium ---')
                task = run_command_in_thread(ice.purge_gas_box_and_sample_line, (), '--- Done purging gas box and sample space  with helium  ---')
            elif event == 'Pump sample space':
                ice.logger.info('--- Pumping sample space ---')
                task = run_command_in_thread(ice.pump_sample_space, (), '--- Done pumping sample space  ---')
            elif event == 'Cancel current command':
                if task is not None:
                    ice.logger.warning('>>>> Cancelling current command')
                    ice._stop_execution = True
            else:
                pass
        
        # Catch exceptions e.g. from cancelling a current command
        except Exception as e:
            ice.logger.error(f'Error: {e}')
        
        # Read button clicks from the window and store button name in "event"
        event, values = window.Read(timeout = 100)
        if event in (None, 'Exit'):         # checks if user wants to 
            exit
            break
        
        # If 'user-initials' has changed, update the logger
        if user_initials != values['user-initials']:
            user_initials = values['user-initials']
            ice.logger = logging.LoggerAdapter(ice.logger.logger, extra = {'user-initials':user_initials})
        
        erase_update_lines(window)
        
        # Check to see whether any tasks are running, and enable/disable buttons accordingly
        if task is not None:
            if task.is_alive():
                [b.update(disabled=True) for b in buttons] # Disable all buttons
                button_cancel.update(disabled=False)
            elif not task.is_alive():
                task = None
                ice._stop_execution = False
                [b.update(disabled=False) for b in buttons] # Enable all buttons
        else:
            if user_initials == '':
                [b.update(disabled=True) for b in buttons] # Disable all buttons
            else:
                [b.update(disabled=False) for b in buttons] # Enable all buttons
                
    ice.ice_disconnect()
    window.Close()



if __name__ == '__main__':  
    
    # Hide the console window that pops up
    import ctypes
    kernel32 = ctypes.WinDLL('kernel32')
    user32 = ctypes.WinDLL('user32')
    SW_HIDE = 0
    hWnd = kernel32.GetConsoleWindow()
    user32.ShowWindow(hWnd, SW_HIDE)
    
    # Connect to the instrument
    ice = IceOxfordDryIce()
    time.sleep(1)
    ice_gui(ice)


#%%

