from trading_platform.infrastructure.persistence.uow.in_memory_unit_of_work import InMemoryUnitOfWork

def test_in_memory_unit_of_work():
    uow = InMemoryUnitOfWork()
    uow.commit()
    assert uow.committed
