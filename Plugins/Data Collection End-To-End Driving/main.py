from ETS2LA.Plugin import *
from ETS2LA.UI import *
import logging


RED = "\033[91m"
NORMAL = "\033[0m"


def DeletePair(Name=""):
    try:
        os.remove(f"{variables.PATH}Data-Collection-End-To-End-Driving/{str(Name)}")
    except OSError as e:
        logging.exception("Failed to remove JSON file %s: %s", Name, e)
    try:
        os.remove(f"{variables.PATH}Data-Collection-End-To-End-Driving/{str(Name).replace('.json', '.png')}")
    except OSError as e:
        logging.exception("Failed to remove image file for %s: %s", Name, e)


def CheckForUploads():
    try:
        Response = requests.get("https://cdn.ets2la.com/", timeout=3)
        if Response.status_code != 200:
            raise Exception("Couldn't connect to the server.")
    except requests.RequestException as e:
        logging.exception("Connectivity check failed: %s", e)
        return

    CurrentTime = time.time()
    if os.path.exists(f"{variables.PATH}Data-Collection-End-To-End-Driving") == False:
        os.mkdir(f"{variables.PATH}Data-Collection-End-To-End-Driving")

    for File in os.listdir(f"{variables.PATH}Data-Collection-End-To-End-Driving"):
        if str(File).endswith(".json") and str(File).replace(".json", ".png") not in os.listdir(f"{variables.PATH}Data-Collection-End-To-End-Driving"):
            try:
                os.remove(f"{variables.PATH}Data-Collection-End-To-End-Driving/{str(File)}")
            except OSError as e:
                logging.exception("Failed to remove unmatched JSON file %s: %s", File, e)
        if str(File).endswith(".png") and str(File).replace(".png", ".json") not in os.listdir(f"{variables.PATH}Data-Collection-End-To-End-Driving"):
            try:
                os.remove(f"{variables.PATH}Data-Collection-End-To-End-Driving/{str(File)}")
            except OSError as e:
                logging.exception("Failed to remove unmatched image file %s: %s", File, e)

    FilesReadyForUpload = []
    for File in os.listdir(f"{variables.PATH}Data-Collection-End-To-End-Driving"):
        if str(File).endswith(".json"):
            try:
                with open(f"{variables.PATH}Data-Collection-End-To-End-Driving/{str(File)}", "r") as F:
                    Data = json.load(F)

                Time = float(Data["Time"])
                if Time + 604800 < CurrentTime:
                    FilesReadyForUpload.append(str(File))

                if "CameraX" not in Data:
                    raise Exception("The data file is missing the 'CameraX' key. Can't upload the data.")

            except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
                logging.exception("Failed to process data file %s: %s", File, e)
                DeletePair(Name=File)

    for File in FilesReadyForUpload:
        try:
            print(f"Data Collection End-To-End Driving: Uploading {File}...")
            Files = [
                ("files", open(f"{variables.PATH}Data-Collection-End-To-End-Driving/{str(File)}", "r")),
                ("files", open(f"{variables.PATH}Data-Collection-End-To-End-Driving/{str(File).replace('.json', '.png')}", "rb"))
            ]
            Response = requests.post(
                f"https://cdn.ets2la.com/datasets/OleFranz/End-To-End/upload/{DataID}", files=Files, timeout=30
            )
            for F in Files:
                F[1].close()
            if "success" in Response.json():
                DeletePair(Name=File)
                print(f"Data Collection End-To-End Driving: Uploaded {File}!")
            elif "error" in Response.json():
                if "Server storage is full." in Response.json()["error"]:
                    DeletePair(Name=File)
        except (requests.RequestException, OSError, json.JSONDecodeError) as e:
            logging.exception("Failed to upload %s: %s", File, e)
            DeletePair(Name=File)


def GetDataID():
    import ETS2LA.variables as variables
    import requests
    import os
    DataID = None
    if os.path.exists(f"{variables.PATH}End-To-End-Data-ID.txt"):
        try:
            with open(f"{variables.PATH}End-To-End-Data-ID.txt", "r") as File:
                Content = File.read()
                DataID = Content.replace("\n", "").replace(" ", "").split(">")[0]
        except OSError as e:
            try:
                os.remove(f"{variables.PATH}End-To-End-Data-ID.txt")
            except OSError as remove_error:
                logging.exception("Failed to remove invalid ID file: %s", remove_error)
            logging.exception("Failed to read data ID: %s", e)
            DataID = None
    if DataID == None:
        try:
            Response = requests.get(
                f"https://cdn.ets2la.com/datasets/OleFranz/End-To-End/get-id"
            ).json()
            if "success" in Response:
                DataID = Response["success"]
            else:
                raise Exception("Couldn't get an ID from the server.")
        except (requests.RequestException, ValueError) as e:
            logging.exception("Failed to retrieve data ID: %s", e)
            return "None"
        with open(f"{variables.PATH}End-To-End-Data-ID.txt", "w") as File:
            File.write(DataID + """
> DO NOT EDIT THIS FILE <
This is the ID used to request the deletion of your data from the End-To-End Driving dataset.
This ID is not public, you can request to delete all data that was collected with this ID by going to https://cdn.ets2la.com/datasets/OleFranz/End-To-End/delete/{your_data_id} or by deleting in the Data Collection End-To-End Driving plugin settings.
If other people get this ID, they can request to delete your data. No personal information is saved with this ID.
If you lose your data ID, you can't request to delete the data collected by you with that ID.
Server side code can be found at https://github.com/ETS2LA/cdn""")
    return DataID


# class SettingsMenu(ETS2LASettingsMenu):
#     dynamic = True
#     plugin_name = "plugin.datacollectionendtoenddriving"
#     
#     def DeleteDataOnPC(self):
#         try:
#             import ETS2LA.variables as variables
#             import os
#             SendPopup("data_collection_end_to_end_driving.deleting_data")
#             if os.path.exists(f"{variables.PATH}Data-Collection-End-To-End-Driving"):
#                 for File in os.listdir(f"{variables.PATH}Data-Collection-End-To-End-Driving"):
#                     try:
#                         os.remove(f"{variables.PATH}Data-Collection-End-To-End-Driving/{str(File)}")
#                     except:
#                         pass
#             SendPopup("data_collection_end_to_end_driving.deleted")
#         except:
#             SendPopup("data_collection_end_to_end_driving.couldnt_delete")
# 
#     def DeleteDataOnServer(self):
#         try:
#             import requests
#             SendPopup("data_collection_end_to_end_driving.deleting_data")
#             Response = requests.get(f"https://cdn.ets2la.com/datasets/OleFranz/End-To-End/delete/{GetDataID()}", timeout=3)
#             if "success" in Response.json() and Response.status_code == 200:
#                 SendPopup("data_collection_end_to_end_driving.deleted")
#             else:
#                 SendPopup("data_collection_end_to_end_driving.couldnt_delete")
#         except:
#             SendPopup("data_collection_end_to_end_driving.couldnt_delete")
# 
#     def render(self):
#         import ETS2LA.variables as variables
#         with Group("vertical", gap=14, padding=0):
#             Title("data_collection_end_to_end_driving.title")
#             Description("data_collection_end_to_end_driving.description")
#             Link("data_collection_end_to_end_driving.link", "https://huggingface.co/OleFranz/End-To-End/tree/main/files", classname="text-muted-foreground")
#         with TabView():
#             with Tab("data_collection_end_to_end_driving.tab.notice"):
#                 Label("data_collection_end_to_end_driving.subtitle")
#                 with Group("vertical", gap=4, padding=0):
#                     Label("data_collection_end_to_end_driving.what_we_send")
#                     Description("data_collection_end_to_end_driving.what_we_send.description")
#                     
#                 with Group("vertical", gap=4, padding=0):
#                     Label("data_collection_end_to_end_driving.what_you_should_know")
#                     Description("data_collection_end_to_end_driving.what_you_should_know.description")
#                     
#                 with Group("vertical", gap=4, padding=0):
#                     Label("data_collection_end_to_end_driving.what_you_can_do")
#                     Description("data_collection_end_to_end_driving.what_you_can_do.description")
#                     
#                 with Group("vertical", gap=4, padding=0):
#                     Label("data_collection_end_to_end_driving.where_the_data_is_saved")
#                     Description(f"• {variables.PATH}Data-Collection-End-To-End-Driving")
#                 
#                 with Group("vertical", gap=4, padding=0):
#                     Label("data_collection_end_to_end_driving.your_current_id")
#                     Description(f"• {GetDataID()}")
#                     
#                 with Group("vertical", gap=4, padding=0):
#                     Label("data_collection_end_to_end_driving.manual_deletion")
#                     Description("data_collection_end_to_end_driving.manual_deletion.description")
#                     Link(f"• https://cdn.ets2la.com/datasets/OleFranz/End-To-End/delete/{GetDataID()}", f"https://cdn.ets2la.com/datasets/OleFranz/End-To-End/delete/{GetDataID()}", classname="text-muted-foreground")
# 
#                 Toggle("data_collection_end_to_end_driving.i_read_the_notice", "i_read_the_notice", default=None)
#                 Space(10)
#                 
#             with Tab("data_collection_end_to_end_driving.tab.control_your_data"):
#                 Button("data_collection_end_to_end_driving.button.delete", "data_collection_end_to_end_driving.delete_data_on_pc.name", self.DeleteDataOnPC, description="data_collection_end_to_end_driving.delete_data_on_pc.description")
#                 Button("data_collection_end_to_end_driving.button.delete", "data_collection_end_to_end_driving.delete_data_on_server.name", self.DeleteDataOnServer, description="data_collection_end_to_end_driving.delete_data_on_server.description")
#                 Description("data_collection_end_to_end_driving.server_code_link.description")
#         return RenderUI()


class Plugin(ETS2LAPlugin):
    description = PluginDescription(
        name="plugin.datacollectionendtoenddriving",
        version="1.0",
        description="plugin.datacollectionendtoenddriving.description",
        modules=["TruckSimAPI", "Camera"],
        tags=[],
        fps_cap=10
    )

    author = Author(
        name="Glas42",
        url="https://github.com/OleFranz",
        icon="https://avatars.githubusercontent.com/u/145870870?v=4"
    )

    # settings_menu = SettingsMenu()

    def imports(self):
        global SCSTelemetry, ScreenCapture, variables, datetime, requests, win32con, win32gui, ctypes, json, math, time, cv2, os

        from Modules.TruckSimAPI.main import scsTelemetry as SCSTelemetry
        import Modules.BetterScreenCapture.main as ScreenCapture
        import ETS2LA.Utils.settings as settings
        import ETS2LA.variables as variables
        import threading
        import datetime
        import requests
        import win32con
        import win32gui
        import ctypes
        import random
        import string
        import json
        import math
        import time
        import cv2
        import os

        global DataID
        global SessionID

        global TruckSimAPI

        global LastCaptureTime
        global LastCaptureLocation

        global LastData
        global LastFrame

        NoticeRead = settings.Get("Data Collection End-To-End Driving", "i_read_the_notice", None)
        if NoticeRead == None:
            self.state.text = "Please read and accept the notice in the settings!"
            while settings.Get("Data Collection End-To-End Driving", "i_read_the_notice", None) == None:
                time.sleep(0.5)
            NoticeRead = settings.Get("Data Collection End-To-End Driving", "i_read_the_notice", None)
            self.state.text = ""
        if NoticeRead != True:
            self.terminate()

        # This ID is not public, you can request to delete all data that was collected with this ID by going to https://cdn.ets2la.com/datasets/OleFranz/End-To-End/delete/{your_data_id}
        # If other people get this ID, they can request to delete your data. No personal information is saved with this ID.
        # If you lose your data ID, you can't request to delete the data collected by you with that ID.
        # Server side code can be found at https://github.com/ETS2LA/cdn
        DataID = GetDataID()
        if DataID == "None":
            print(f"\n{RED}Unable to do data collection, couldn't get a response from the server. The plugin will disable itself.{NORMAL}\n")
            self.terminate()


        # This ID is saved with the data publicly, it's used to make sorting data easier
        SessionID = str("".join(random.choices(str(string.ascii_letters + string.digits + "-_"), k=15)))


        TruckSimAPI = SCSTelemetry()

        LastCaptureTime = 0
        LastCaptureLocation = 0, 0, 0

        LastData = None
        LastFrame = None

        X1, Y1, X2, Y2 = ScreenCapture.GetWindowPosition(Name="Truck Simulator", Blacklist=["Discord"])
        Screen = ScreenCapture.GetScreenIndex((X1 + X2) / 2, (Y1 + Y2) / 2)
        ScreenCapture.Initialize(Screen=Screen - 1, Area=(X1, Y1, X2, Y2))

        threading.Thread(target=CheckForUploads, daemon=True).start()

    def run(self):
        CurrentTime = time.time()

        global TruckSimAPI

        global LastCaptureTime
        global LastCaptureLocation

        global LastData
        global LastFrame


        APIDATA = TruckSimAPI.update()

        CurrentLocation = APIDATA["truckPlacement"]["coordinateX"], APIDATA["truckPlacement"]["coordinateY"], APIDATA["truckPlacement"]["coordinateZ"]

        RouteAdvisor = ScreenCapture.ClassifyRouteAdvisor(Name="Truck Simulator", Blacklist=["Discord"])
        if (RouteAdvisor[0][0] >= 0.9 and RouteAdvisor[0][1] >= 0.9 and RouteAdvisor[0][2] >= 0.9) or (RouteAdvisor[1][0] >= 0.9 and RouteAdvisor[1][1] >= 0.9 and RouteAdvisor[1][2] >= 0.9):
            RouteAdvisorCorrect = True
        else:
            RouteAdvisorCorrect = False

        AlwaysOnTopWindows = []
        win32gui.EnumWindows(lambda HWND, _: AlwaysOnTopWindows.append(HWND) if win32gui.IsWindowVisible(HWND) and (win32gui.GetWindowLong(HWND, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOPMOST) else None, None)
        AppIsAlwaysOnTop = False
        for Window in AlwaysOnTopWindows:
            if str(win32gui.GetWindowText(Window)) == variables.APPTITLE:
                AppIsAlwaysOnTop = True
                break

        ARAffinitySet = False
        HWND = win32gui.FindWindow(None, "ETS2LA AR Overlay")
        if HWND != 0:
            Affinity = ctypes.wintypes.DWORD()
            Success = ctypes.windll.user32.GetWindowDisplayAffinity(HWND, ctypes.byref(Affinity))
            if Success:
                if int(Affinity.value) != 0:
                    ARAffinitySet = True
        else:
            ARAffinitySet = True

        if (CurrentTime - LastCaptureTime < 3 or
            math.sqrt((LastCaptureLocation[0] - CurrentLocation[0])**2 + (LastCaptureLocation[1] - CurrentLocation[1])**2 + (LastCaptureLocation[2] - CurrentLocation[2])**2) < 0.5):
            return

        if (ScreenCapture.IsForegroundWindow(Name="Truck Simulator", Blacklist=["Discord"]) == False or
            RouteAdvisorCorrect == False or
            AppIsAlwaysOnTop == True or
            ARAffinitySet == False or
            APIDATA["sdkActive"] == False or
            APIDATA["pause"] == True):
            LastData = None
            LastFrame = None
            time.sleep(0.2)
            return


        LastCaptureTime = CurrentTime
        LastCaptureLocation = APIDATA["truckPlacement"]["coordinateX"], APIDATA["truckPlacement"]["coordinateY"], APIDATA["truckPlacement"]["coordinateZ"]


        ScreenCapture.TrackWindow(Name="Truck Simulator", Blacklist=["Discord"])

        Frame = ScreenCapture.Capture(ImageType="cropped")
        if type(Frame) == type(None) or Frame.shape[0] <= 0 or Frame.shape[1] <= 0:
            return


        RouteAdvisorSide = str(ScreenCapture.RouteAdvisorSide)
        RouteAdvisorZoomCorrect = bool(ScreenCapture.RouteAdvisorZoomCorrect)
        RouteAdvisorTabCorrect = bool(ScreenCapture.RouteAdvisorTabCorrect)

        Game = str(APIDATA["scsValues"]["game"]).lower()

        Speed = float(APIDATA["truckFloat"]["speed"])
        SpeedLimit = float(APIDATA["truckFloat"]["speedLimit"])
        CruiseControlEnabled = bool(APIDATA["truckBool"]["cruiseControl"])
        CruiseControlSpeed = float(APIDATA["truckFloat"]["cruiseControlSpeed"])

        Steering = float(APIDATA["truckFloat"]["gameSteer"])
        Throttle = float(APIDATA["truckFloat"]["gameThrottle"])
        Brake = float(APIDATA["truckFloat"]["gameBrake"])
        Clutch = float(APIDATA["truckFloat"]["gameClutch"])

        ParkBrake = bool(APIDATA["truckBool"]["parkBrake"])
        Wipers = bool(APIDATA["truckBool"]["wipers"])
        Gear = int(APIDATA["truckInt"]["gear"])
        Gears = int(APIDATA["configUI"]["gears"])
        ReverseGears = int(APIDATA["configUI"]["gearsReverse"])
        EngineRPM = float(APIDATA["truckFloat"]["engineRpm"])

        LeftIndicator = bool(APIDATA["truckBool"]["blinkerLeftActive"])
        RightIndicator = bool(APIDATA["truckBool"]["blinkerRightActive"])
        HazardLights = bool(APIDATA["truckBool"]["lightsHazard"])
        ParkingLights = bool(APIDATA["truckBool"]["lightsParking"])
        LowBeamLights = bool(APIDATA["truckBool"]["lightsBeamLow"])
        HighBeamLights = bool(APIDATA["truckBool"]["lightsBeamHigh"])
        BeaconLights = bool(APIDATA["truckBool"]["lightsBeacon"])
        BrakeLights = bool(APIDATA["truckBool"]["lightsBrake"])
        ReverseLights = bool(APIDATA["truckBool"]["lightsReverse"])

        PositionX = float(APIDATA["truckPlacement"]["coordinateX"])
        PositionY = float(APIDATA["truckPlacement"]["coordinateY"])
        PositionZ = float(APIDATA["truckPlacement"]["coordinateZ"])
        RotationX = float(APIDATA["truckPlacement"]["rotationX"])
        RotationY = float(APIDATA["truckPlacement"]["rotationY"])
        RotationZ = float(APIDATA["truckPlacement"]["rotationZ"])

        CabinX = float(APIDATA["headPlacement"]["cabinOffsetX"] + APIDATA["configVector"]["cabinPositionX"])
        CabinY = float(APIDATA["headPlacement"]["cabinOffsetY"] + APIDATA["configVector"]["cabinPositionY"])
        CabinZ = float(APIDATA["headPlacement"]["cabinOffsetZ"] + APIDATA["configVector"]["cabinPositionZ"])
        CabinRotationX = float(APIDATA["headPlacement"]["cabinOffsetrotationX"])
        CabinRotationY = float(APIDATA["headPlacement"]["cabinOffsetrotationY"])
        CabinRotationZ = float(APIDATA["headPlacement"]["cabinOffsetrotationZ"])

        HeadX = float(APIDATA["headPlacement"]["headOffsetX"] + APIDATA["configVector"]["headPositionX"] + APIDATA["headPlacement"]["cabinOffsetX"] + APIDATA["configVector"]["cabinPositionX"])
        HeadY = float(APIDATA["headPlacement"]["headOffsetY"] + APIDATA["configVector"]["headPositionY"] + APIDATA["headPlacement"]["cabinOffsetY"] + APIDATA["configVector"]["cabinPositionY"])
        HeadZ = float(APIDATA["headPlacement"]["headOffsetZ"] + APIDATA["configVector"]["headPositionZ"] + APIDATA["headPlacement"]["cabinOffsetZ"] + APIDATA["configVector"]["cabinPositionZ"])
        HeadRotationX = float(APIDATA["headPlacement"]["headOffsetrotationX"])
        HeadRotationY = float(APIDATA["headPlacement"]["headOffsetrotationY"])
        HeadRotationZ = float(APIDATA["headPlacement"]["headOffsetrotationZ"])


        Camera = self.modules.Camera.run()
        if Camera is not None:
            FOV = Camera.fov
            Angles = Camera.rotation.euler()
            CameraX = Camera.position.x + Camera.cx * 512
            CameraY = Camera.position.y
            CameraZ = Camera.position.z + Camera.cz * 512
            CameraRotationDegreesX = Angles[1]
            CameraRotationDegreesY = Angles[0]
            CameraRotationDegreesZ = Angles[2]


        Data = {
            "Time": CurrentTime,
            "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "SessionID": SessionID,
            "FOV": FOV,
            "RouteAdvisorSide": RouteAdvisorSide,
            "RouteAdvisorZoomCorrect": RouteAdvisorZoomCorrect,
            "RouteAdvisorTabCorrect:": RouteAdvisorTabCorrect,
            "Game": Game,
            "Speed": Speed,
            "SpeedLimit": SpeedLimit,
            "CruiseControlEnabled": CruiseControlEnabled,
            "CruiseControlSpeed": CruiseControlSpeed,
            "Steering": Steering,
            "Throttle": Throttle,
            "Brake": Brake,
            "Clutch": Clutch,
            "ParkBrake": ParkBrake,
            "Wipers": Wipers,
            "Gear": Gear,
            "Gears": Gears,
            "ReverseGears": ReverseGears,
            "EngineRPM": EngineRPM,
            "LeftIndicator": LeftIndicator,
            "RightIndicator": RightIndicator,
            "HazardLights": HazardLights,
            "ParkingLights": ParkingLights,
            "LowBeamLights": LowBeamLights,
            "HighBeamLights": HighBeamLights,
            "BeaconLights": BeaconLights,
            "BrakeLights": BrakeLights,
            "ReverseLights": ReverseLights,
            "CameraX": CameraX,
            "CameraY": CameraY,
            "CameraZ": CameraZ,
            "CameraRotationDegreesX": CameraRotationDegreesX,
            "CameraRotationDegreesY": CameraRotationDegreesY,
            "CameraRotationDegreesZ": CameraRotationDegreesZ,
            "PositionX": PositionX,
            "PositionY": PositionY,
            "PositionZ": PositionZ,
            "RotationX": RotationX,
            "RotationY": RotationY,
            "RotationZ": RotationZ,
            "CabinX": CabinX,
            "CabinY": CabinY,
            "CabinZ": CabinZ,
            "CabinRotationX": CabinRotationX,
            "CabinRotationY": CabinRotationY,
            "CabinRotationZ": CabinRotationZ,
            "HeadX": HeadX,
            "HeadY": HeadY,
            "HeadZ": HeadZ,
            "HeadRotationX": HeadRotationX,
            "HeadRotationY": HeadRotationY,
            "HeadRotationZ": HeadRotationZ
        }


        if os.path.exists(f"{variables.PATH}Data-Collection-End-To-End-Driving") == False:
            os.mkdir(f"{variables.PATH}Data-Collection-End-To-End-Driving")

        if LastData != None:
            Name = str(CurrentTime)

            with open(f"{variables.PATH}Data-Collection-End-To-End-Driving/{Name}.json", "w") as F:
                json.dump(LastData, F, indent=4)

            cv2.imwrite(f"{variables.PATH}Data-Collection-End-To-End-Driving/{Name}.png", LastFrame, [int(cv2.IMWRITE_PNG_COMPRESSION), 9])

        LastData = Data.copy()
        LastFrame = Frame.copy()
