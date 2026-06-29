from trading_platform.infrastructure.transactions.transaction_manager import TransactionManager

class Uow:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

def test_transaction_manager_commit():
    uow = Uow()
    tm = TransactionManager(uow)
    assert tm.execute(lambda: "ok") == "ok"
    assert uow.committed
    assert not uow.rolled_back
