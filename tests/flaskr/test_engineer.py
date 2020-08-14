from agent_pi.bt_search_subprocess import matchfound_callback as bt_matchfound
# from agent_pi.qr_code_subprocess import matchfound_callback as qr_matchfound
# from master_pi.grpc import masterclient


def test_engineer_resolve_report(start_car_service):
    _ = start_car_service(1)
    bt_matchfound()


def test_engineer_view_reports():
    pass


def test_engineer_enable_bluetooth():
    pass


def test_engineer_lock_car():
    pass
