from ETS2LA.UI import *

from ETS2LA.Events.classes import Job, CancelledJob, FinishedJob, Refuel
from Modules.SDKController.main import SCSController
import ETS2LA.Events.log_reader as log_reader
from ETS2LA.Networking.Servers.notifications import dialog
import ETS2LA.Handlers.plugins as plugins
import ETS2LA.Networking.cloud as cloud
import Modules.TruckSimAPI.main as API
import threading
import logging
import time

import ETS2LA.Utils.settings as settings

API = API.Module("global") # type: ignore # This is a hack but it works.
API.CHECK_EVENTS = True # DO NOT DO THIS ANYWHERE ELSE!!! PLEASE USE THE EVENTS SYSTEM INSTEAD!!!
api_callbacks = []
log_callbacks = []
controller = SCSController()

steering_threshold = settings.Get("global", "steering_threshold", 0.1)
braking_threshold = settings.Get("global", "braking_threshold", 0.2)
    
# Events
last_started_job = None # This is used to fill out the data for the Job events
class JobStarted():
    def JobStarted(self, data):
        global last_started_job
        job = Job()
        job.fromAPIData(data)
        plugins.call_event('JobStarted', [job], {})
        logging.info("Triggered event: [dim]JobStarted[/dim]")
        cloud.StartedJob(job)
        last_started_job = job
    def __init__(self):
        API.listen('jobStarted', self.JobStarted) # type: ignore
        
class JobFinished():
    def JobFinished(self, data):
        job = FinishedJob()
        job.fromAPIData(data)
        if job.cargo_id == '' and job.cargo == '' and job.unit_count == 0 and job.unit_mass == 0 and last_started_job != None:
            job.cargo_id = last_started_job.cargo_id
            job.cargo = last_started_job.cargo
            job.unit_count = last_started_job.unit_count
            job.unit_mass = last_started_job.unit_mass
            
        class CargoDialog(ETS2LADialog):
            def render(self):
                with Form():
                    Title("Job finished!")
                    Description(f"Here are some stats:")
                    with TabView():
                        with Tab("General"):
                            Space(1)
                            with Group("vertical"):
                                with Group("horizontal"):
                                    with Group("vertical"):
                                        Label("Cargo")
                                        Description(job.cargo)
                                    with Group("vertical"):
                                        Label("Cargo ID")
                                        Description(job.cargo_id)
                                with Group("horizontal"):
                                    with Group("vertical"):
                                        Label("Unit mass")
                                        Description(str(round(job.unit_mass)))
                                    with Group("vertical"):
                                        Label("Unit count")
                                        Description(str(round(job.unit_count)))
                                with Group("horizontal"):
                                    with Group("vertical"):
                                        Label("Starting time")
                                        Description(str(round(job.starting_time)))
                                    with Group("vertical"):
                                        Label("Finished time")
                                        Description(str(round(job.finished_time)))
                                with Group("horizontal"):
                                    with Group("vertical"):
                                        Label("Delivery time")
                                        Description(str(round(job.delivered_delivery_time)))
                                    with Group("vertical"):
                                        Label("Autoload used")
                                        Description(str(job.delivered_autoload_used))
                                        
                        with Tab("Computed"):
                            with Group("vertical"):
                                with Group("horizontal"):
                                    with Group("vertical"):
                                        Label("Total weight")
                                        Description(str(round(job.unit_mass * job.unit_count)) + " kg")
                                    with Group("vertical"):
                                        Label("Total revenue")
                                        Description(str(round(job.delivered_revenue)) + " €")
                                with Group("horizontal"):
                                    with Group("vertical"):
                                        Label("Revenue per km")
                                        if job.delivered_distance_km == 0 or job.delivered_revenue == 0:
                                            Description("0 €")
                                        else:
                                            Description(str(round(job.delivered_revenue / job.delivered_distance_km, 2)) + " €")
                                    with Group("vertical"):
                                        Label("Revenue per hour")
                                        if job.finished_time == 0 or job.delivered_revenue == 0:
                                            Description("0 €")
                                        else:
                                            Description(str(round(job.delivered_revenue / (job.finished_time / 60))) + " €")
                                with Group("horizontal"):
                                    with Group("vertical"):
                                        Label("Revenue per ton")
                                        if job.unit_mass == 0 or job.unit_count == 0:
                                            Description("0 €")
                                        else:
                                            Description(str(round(job.delivered_revenue / (job.unit_mass * job.unit_count / 1000))) + " €")
                                    with Group("vertical"):
                                        Label("Average speed")
                                        if job.finished_time == 0 or job.delivered_distance_km == 0:
                                            Description("0 km/h")
                                        else:
                                            Description(str(round(job.delivered_distance_km / ((job.finished_time - job.starting_time) / 60), 1)) + " km/h")
                            
                return RenderUI()
        plugins.call_event('JobFinished', [job], {})
        logging.info("Triggered event: [dim]JobFinished[/dim]")
        cloud.FinishedJob(job)
        dialog(CargoDialog().build())
    def __init__(self):
        API.listen('jobFinished', self.JobFinished) # type: ignore
        
class JobDelivered():
    def JobDelivered(self, data):
        job = FinishedJob()
        job.fromAPIData(data)
        plugins.call_event('JobDelivered', [job], {})
        logging.info("Triggered event: [dim]JobDelivered[/dim]")
    def __init__(self):
        API.listen('jobDelivered', self.JobDelivered) # type: ignore
        
class JobCancelled():
    def JobCancelled(self, data):
        job = CancelledJob()
        job.fromAPIData(data)
        plugins.call_event('JobCancelled', [job], {})
        logging.info("Triggered event: [dim]JobCancelled[/dim]")
        cloud.CancelledJob(job)
    def __init__(self):
        API.listen('jobCancelled', self.JobCancelled) # type: ignore
        
class RefuelStarted():
    def RefuelStarted(self, data):
        refuel = Refuel()
        refuel.fromAPIData(data)
        plugins.call_event('RefuelStarted', [refuel], {})
        logging.info("Triggered event: [dim]RefuelStarted[/dim]")
    def __init__(self):
        API.listen('refuelStarted', self.RefuelStarted) # type: ignore
        
class RefuelPayed():
    def RefuelPayed(self, data):
        refuel = Refuel()
        refuel.fromAPIData(data)
        plugins.call_event('RefuelPayed', [refuel], {})
        logging.info("Triggered event: [dim]RefuelPayed[/dim]")
    def __init__(self):
        API.listen('refuelPayed', self.RefuelPayed) # type: ignore

class VehicleChange():
    lastLicensePlate = ""
    def VehicleChange(self, data):
        plugins.call_event('VehicleChange', data["configString"]["truckLicensePlate"], {})
        logging.info("Triggered event: [dim]VehicleChange[/dim]")
        
    def ApiCallback(self, data):
        if data["configString"]["truckLicensePlate"] != self.lastLicensePlate:
            self.lastLicensePlate = data["configString"]["truckLicensePlate"]
            self.VehicleChange(data)
        
    def __init__(self):
        api_callbacks.append(self.ApiCallback)
        
class GameShutdown():
    def GameShutdown(self, lines):
        start_found = False
        end_found = False
        for line in lines:
            if "[sys] running on" in line:
                start_found = True
            if "[sys] Process manager shutdown" in line:
                end_found = True
        
        if end_found and not start_found:
            plugins.call_event('GameShutdown', [None], {})
            logging.info("Triggered event: [dim]GameShutdown[/dim]")
            SendPopup("Detected game shutdown", "info")
            return
    
    def __init__(self):
        log_callbacks.append(self.GameShutdown)
        
class GameStart():
    def GameStart(self, lines):
        start_found = False
        end_found = False
        for line in lines:
            if "[sys] running on" in line:
                start_found = True
            if "[sys] Process manager shutdown" in line:
                end_found = True
                
        if start_found and not end_found:
            plugins.call_event('GameStart', [None], {})
            logging.info("Triggered event: [dim]GameStart[/dim]")
            SendPopup("Detected game start", "info")
    
    def __init__(self):
        log_callbacks.append(self.GameStart)
        
class DetectCrackedGame():
    def DetectCrackedGame(self, lines):
        identifier = "0000007E"
        for line in lines:
            if identifier in line:
                plugins.call_event('DetectCrackedGame', [None], {})
                logging.info("Triggered event: [dim]DetectCrackedGame[/dim]")
                class CrackedDialog(ETS2LADialog):
                    def render(self):
                        with Form():
                            Title("Detected Cracked Game")
                            Description("ETS2LA will not work on cracked games (or DLCs). Please purchase the game on steam. This is due to a limitation in the way the cracked games are made. We can't do anything about it.\n\nPlease note that there can be false positives from broken mods or plugins. We don't implement software locks, if the app works then you can ignore this message.")
                            Space(8)
                            
                        return RenderUI()
                    
                dialog(CrackedDialog().build())
                return
            
    def __init__(self):
        log_callbacks.append(self.DetectCrackedGame)
        
class DetourGenerated():
    def DetourGenerated(self, lines):
        identifier = "[detour] Detour generation started at item:"
        for line in lines:
            if identifier in line:
                item = line.split(identifier)[1].strip()
                plugins.call_event('DetourGenerated', item, {})
                logging.info("Triggered event: [dim]DetourGenerated[/dim]({})".format(item))
                SendPopup("Detour generated, original route might be invalid.", "warning")
                return
        
    def __init__(self):
        log_callbacks.append(self.DetourGenerated)
        
# Start monitoring
def ApiThread():
    while True:
        data = API.run() # type: ignore
        for callback in api_callbacks:
            try:
                callback(data)
            except Exception as e:
                logging.exception("Error in callback: %s", e)
                
        time.sleep(0.1)
        
def LogThread():
    first_time = True
    while True:
        new_lines = log_reader.update()
        if first_time and len(new_lines) > 0:
            first_time = False
            logging.info("Log reader started")
            SendPopup("Started reading game logs.", "info")
            
        for callback in log_callbacks:
            try:
                callback(new_lines)
            except Exception as e:
                logging.exception("Error in callback: %s", e)
        
        time.sleep(0.1)

def run():
    JobStarted()
    JobFinished()
    JobDelivered()
    JobCancelled()
    RefuelStarted()
    RefuelPayed()
    VehicleChange()
    GameShutdown()
    GameStart()
    DetectCrackedGame()
    DetourGenerated()
    
    threading.Thread(target=ApiThread, daemon=True).start()
    threading.Thread(target=LogThread, daemon=True).start()
    logging.info("Event monitor started.")
