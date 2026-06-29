class TransactionManager:
    def __init__(self, unit_of_work) -> None:
        self.unit_of_work = unit_of_work

    def execute(self, operation):
        try:
            result = operation()
            self.unit_of_work.commit()
            return result
        except Exception:
            self.unit_of_work.rollback()
            raise
