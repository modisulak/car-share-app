from agent_pi.utils import MASTERSERVICE_IP
from css_rpc import car_share_pb2_grpc, car_share_pb2
import grpc


def unlock_callback(user_credentials_request):
    masterservice_ip = MASTERSERVICE_IP()
    print("contacting masterservice {}".format(masterservice_ip))
    with grpc.insecure_channel(masterservice_ip) as channel:
        stub = car_share_pb2_grpc.MasterServiceStub(channel)
        response = stub.UnlockCarRequest(
            car_share_pb2.UserCredentialsRequest(**user_credentials_request))
    print(response)


def resolve_report_callback(user_credentials_request, report_id):
    masterservice_ip = MASTERSERVICE_IP()
    print("contacting masterservice {}".format(masterservice_ip))
    with grpc.insecure_channel(masterservice_ip) as channel:
        stub = car_share_pb2_grpc.MasterServiceStub(channel)
        user = car_share_pb2.UserCredentialsRequest(**user_credentials_request)
        response = stub.ResolveCarReport(
            car_share_pb2.CarReportRequest(user=user, report_id=report_id))
    return response
