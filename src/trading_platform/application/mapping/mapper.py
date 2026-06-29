class Mapper:
    def map(self, source, target_type):
        return target_type(**vars(source))
