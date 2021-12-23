class DbConnectionInterface:
    def on_db_connection(self):
        raise NotImplementedError

    def on_db_connection_loss(self):
        raise NotImplementedError
