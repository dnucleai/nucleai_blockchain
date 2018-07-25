import threading
import time
import grpc
import traceback
import nucleai_pb2 as pb
import nucleai_pb2_grpc as pb_grpc
from logger import singleton as log
from concurrent import futures
import random

from collections import deque, defaultdict


PHASE_NONE = 0
PHASE_TRAIN = 1
PHASE_UPDATE = 2

class Learner:

    class Exception(Exception):
        pass

    # private methods are run inside a separate thread
    # public methods interact with that thread safely

    # I use Python native stuff here instead of PyTorch tensors of Numpy arrays
    #   TODO optimize later if needed 

    def __init__(self, initial_parameters_f, starting_cycle_time=15):
        self.parameters = None
        self.initial_parameters_f = initial_parameters_f
        self.dropout_ratio = 0.25 # fraction of params selected for download and upload

        self.cycle_id = 1
        self.cycle_time = starting_cycle_time
        self.clock = None
        self.phase = PHASE_NONE
        self.upload_q = deque()
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True # so the thread halts if the parent halts

    def _train_phase(self):
        self.phase = PHASE_TRAIN
        self.parameters = self.initial_parameters_f()

        while self.clock > 0:
            time.sleep(1)
            self.clock -= 1

    def _update_phase(self):
        self.phase = PHASE_UPDATE
        uploads = list(self.upload_q)
        self.upload_q.clear()
        for upload in uploads:
            if upload.cycleId.num != self.cycle_id:
                # it's still possible to get something from the wrong cycle here,
                #   so ignore it if it happens
                continue
            deltas = upload.deltas
            for delta in deltas.parameters: # TODO it's just SGD for now
                old = self.parameters[delta.index]
                self.parameters[delta.index] += delta.value 
                log.debug("update phase: param {} changed from {} to {}"
                        .format(delta.index, old, self.parameters[delta.index]))

    def _run_loop(self):
        while True:
            log.debug("Starting cycle {}".format(self.cycle_id))
            self.clock = self.cycle_time
            log.info("Entering download/train phase")
            self._train_phase()
            log.info("Entering update phase")
            self._update_phase() 
            self.cycle_id += 1

    def start(self):
        self.thread.start()

    def download(self, request):
        log.debug("Client {} downloading".format(request.clientId.txt))
        if self.phase != PHASE_TRAIN: # TODO maybe only allow downloads if enough time remaining
            raise self.Exception("cannot download except in the training phase")
        # download a random subset of the parameters
        parameters = [pb.IndexedValue(index=i, value=val) for i, val in random.sample(list(self.parameters.items()), int(len(self.parameters) * self.dropout_ratio))]
        log.debug("all parameters = {}, parameters being downloaded = {}".format(self.parameters, parameters))
        parameters = pb.Parameters(parameters=parameters)
        return pb.DownloadResponse(
                cycleId=pb.CycleId(num=self.cycle_id),
                parameters=parameters,
                )

    def upload(self, request):
        log.debug("Client {} uploading".format(request.clientId.txt))
        # TODO don't let a client upload twice per cycle
        if self.phase != PHASE_TRAIN:
            raise self.Exception("cannot upload except in the training phase")
        if self.cycle_id != request.cycleId.num:
            raise self.Exception("upload is for cycle {}, but server is on cycle {}"
                    .format(request.cycleId.num, self.cycle_id))
        if len(request.deltas.parameters) != int(len(self.parameters) * self.dropout_ratio):
            raise self.Exception("too any or too few deltas uploaded")
        self.upload_q.append(request)
        return pb.UploadResponse()


global_learner = None

class LearningServicer(pb_grpc.LearningServicer):

    def __init__(self):
        pass

    def _try(self, f, context):
        try:
            ret = f()
            return ret
        except Exception as e:
            if isinstance(e, Learner.Exception):
                # bad input, not our fault; send back the exception for the client to see
                log.warn("Invalid input from client, exception: {}".format(e))
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(repr(e))
                return pb.Void()
            else:
                # our fault; log the exception, but don't send it to the client
                log.error("unexpected exception: {}".format(e))
                context.set_code(grpc.StatusCode.ABORTED)
                context.set_details(repr("internal error"))
                return pb.Void()


    # service endpoints, which shall just pass the request on to the parameter server

    def Download(self, request, context):
        def f():
            return global_learner.download(request)
        return self._try(f, context)

    def Upload(self, request, context):
        def f():
            return global_learner.upload(request)
        return self._try(f, context)


def run():

    # start the parameter server
    global global_learner
    initial_parameters_f = (lambda: {i: random.random() for i in range(1, 11)}) # TODO temp
    global_learner = Learner(initial_parameters_f=initial_parameters_f)
    global_learner.start()

    # start the gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb_grpc.add_LearningServicer_to_server(LearningServicer(), server)
    server.add_insecure_port('[::]:1453')
    server.start()
    try:
        while True: # otherwise the script just exits
            print("tick")
            time.sleep(600)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    run()
