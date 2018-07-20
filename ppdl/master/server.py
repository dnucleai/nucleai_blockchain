import threading
import time
import grpc
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

    def __init__(self, initial_weights_f, starting_cycle_time=15):
        self.weights = None
        self.initial_weights_f = initial_weights_f
        self.learning_rate = 1e-6 # TODO
        self.dropout_ratio = 0.25 # fraction of params selected for download and upload

        self.cycle_time = starting_cycle_time
        self.clock = None
        self.phase = PHASE_NONE
        self.upload_q = deque()
        self.thread = threading.Thread(target=self._run_loop)

    def _train_phase(self):
        self.phase = PHASE_TRAIN
        self.weights = self.initial_weights_f()

        while self.clock > 0:
            time.sleep(1)
            self.clock -= 1

    def _update_phase(self):
        self.phase = PHASE_UPDATE
        deltass = list(self.upload_q)
        self.upload_q.clear()
        for deltas in deltass:
            for grad in deltas.gradients: # TODO it's just SGD for now
                old = self.weights[grad.index]
                self.weights[grad.index] -= self.learning_rate * grad.value 
                log.debug("update phase: param {} changed from {} to {}".format(grad.index, old, self.weights[grad.index]))

    def _run_loop(self):
        while True:
            self.clock = self.cycle_time
            log.info("Entering download/train phase...")
            self._train_phase()
            log.info("Entering update phase...")
            self._update_phase() 

    def start(self):
        self.thread.start()

    def upload(self, deltas):
        if self.phase != PHASE_TRAIN:
            raise self.Exception("cannot upload except in the training phase")
        if len(deltas.gradients) != int(len(self.weights) * self.dropout_ratio):
            raise self.Exception("too any or too few deltas uploaded")
        self.upload_q.append(deltas)

    def download(self):
        if self.phase != PHASE_TRAIN:
            raise self.Exception("cannot download except in the training phase")
        # download a random subset of the weights
        weights = [pb.IndexedValue(index=i, value=val) for i, val in random.sample(list(self.weights.items()), int(len(self.weights) * self.dropout_ratio))]
        log.debug("all weights = {}, weights being downloaded = {}".format(self.weights, weights))
        if self.phase != PHASE_TRAIN: # check again, 2-phase commit style
            raise self.Exception("cannot download except in the training phase")
        return pb.Parameters(weights=weights)


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
                # bad input, not our fault
                log.warn("Invalid input from client, exception: {}".format(e))
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(repr(e))
                return pb.Void()
            else:
                # our fault
                log.error("unexpected exception: {}".format(e))
                context.set_code(grpc.StatusCode.ABORTED)
                context.set_details(repr("internal error"))
                return pb.Void()


    def Enqueue(self, request, context):
        def f():
            log.info("Client {} enqueued".format(request.clientId.txt))
            return pb.EnqueueResponse(waitTime=pb.Event(secondsFromNow=global_learner.clock))
        return self._try(f, context)

    def Download(self, request, context):
        def f():
            log.debug("Client {} downloading".format(request.clientId.txt))
            return pb.DownloadResponse(parameters=global_learner.download())
        return self._try(f, context)

    def Upload(self, request, context):
        def f():
            log.debug("Client {} uploading".format(request.clientId.txt))
            global_learner.upload(request.deltas)
            return pb.UploadResponse()
        return self._try(f, context)


def run():
    global global_learner
    global_learner = Learner(initial_weights_f=(lambda: {i: random.random() for i in range(1, 11)}))
    global_learner.start()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb_grpc.add_LearningServicer_to_server(LearningServicer(), server)
    server.add_insecure_port('[::]:1453')
    server.start()
    try:
        while True:
            print("tick")
            time.sleep(60)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    run()
