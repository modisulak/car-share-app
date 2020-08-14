from css_rpc import car_share_pb2, car_share_pb2_grpc
import grpc
from agent_pi.utils import SOCKETS_ENABLED


class MasterClient:
    def __init__(self, agent_ip=None, master_ip=None):
        if SOCKETS_ENABLED():
            if agent_ip:
                self.channel = grpc.insecure_channel(agent_ip)
                self.stub = car_share_pb2_grpc.AgentServiceStub(self.channel)
            elif master_ip:
                self.channel = grpc.insecure_channel(master_ip)
                self.stub = car_share_pb2_grpc.MasterServiceStub(self.channel)
            else:
                raise Exception("target grpc service ip address is null")
        else:
            print("SOCKETS NOT ENABLED, CANNOT MAKE GRPC REQUEST")

    def BTProximityUnlock(self, *_, bd_addr, user):
        if SOCKETS_ENABLED():
            with self.channel:
                response = self.stub.BTProximityUnlock(
                    car_share_pb2.BluetoothUnlockUser(
                        bd_addr=bd_addr,
                        user=car_share_pb2.UserCredentialsRequest(**user)))
            return response

    def SearchBluetooth(self):
        if SOCKETS_ENABLED():
            with self.channel:
                response = self.stub.SearchBluetooth(
                    car_share_pb2.GeneralRequest(data=""))
            return response

    def VoiceRecognitionQuery(self):
        if SOCKETS_ENABLED():
            with self.channel:
                response = self.stub.VoiceRecognitionQuery(
                    car_share_pb2.GeneralRequest(data=""))
            return response

    def LoadUserCredentials(self, id, username, authtoken, user_face_model):
        if SOCKETS_ENABLED():
            with self.channel:
                response = self.stub.LoadUserCredentials(
                    car_share_pb2.UserCredentialsRequest(
                        id=id,
                        username=username,
                        authtoken=authtoken,
                        user_face_model=user_face_model))
            return response

    def SetFaceUnlockStatus(self, status):
        if SOCKETS_ENABLED():
            with self.channel:
                response = self.stub.SetFaceUnlockStatus(
                    car_share_pb2.FaceUnlockStatus(running=bool(status)))
            return response

    def LockCar(self):
        if SOCKETS_ENABLED():
            with self.channel:
                response = self.stub.LockCar(
                    car_share_pb2.GeneralRequest(data=""))
            return response

    def UnlockCar(self):
        if SOCKETS_ENABLED():
            with self.channel:
                response = self.stub.UnlockCar(
                    car_share_pb2.GeneralRequest(data=""))
            return response

    def UnloadUser(self):
        if SOCKETS_ENABLED():
            with self.channel:
                response = self.stub.UnloadUser(
                    car_share_pb2.GeneralRequest(data=""))
            return response

    def ResolveCarReport(self):
        if SOCKETS_ENABLED():
            with self.channel:
                response = self.stub.ResolveCarReport(
                    car_share_pb2.GeneralRequest(data=""))
            return response
