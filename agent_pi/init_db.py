from agent_pi.database import db


def run():
    db.drop_all()
    db.create_all()
    print("initialised Database.")


if __name__ == "__main__":
    run()
