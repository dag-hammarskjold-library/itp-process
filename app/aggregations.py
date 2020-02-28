class Aggregation(object):
    def __init__(self):
        self.bodysession = None
        self.stages = []
        '''
        self.match_stage = None
        self.project_stage = None
        self.unwind_stage = []
        self.transform_stage = None
        self.merge_stage = None
        '''
    
    def exec(self):
        for stage in self.stages:
            stage.exec()
            # Wrap in try ... except and return status.


class Stage(object):
    def __init__(self):
        self.stage_type = None

    def exec(self):
        # do the work
        pass

class MatchStage(Stage):
    # any init data

    def foo(self):
        return 'bar'