#!/usr/bin/env python

from concrete import Communication, LanguageIdentification, UUID, AnnotationMetadata
from concrete.services import Annotator
from concrete.util.concrete_uuid import AnalyticUUIDGeneratorFactory

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TCompactProtocol
from thrift.server import TServer

from valid import languages, model, utils

from glob import glob
import os.path
import re
import time
import uuid
import logging
import pickle

class CommunicationHandler():
    def __init__(self, model_path):
        with open(model_path) as ifd:
            self.classifier = pickle.load(ifd) #model.LidClassifier(model_path)
        #self.classifier = model.LidClassifier(code_lookup=languages.MAP_2_TO_3)
        #for fname in glob(os.path.join(model_path, "*.mod")):
        #    lang, order = re.match(r"^(.*)\.(\d+)\.mod$", os.path.basename(fname)).groups()
        #    self.classifier.add(lang, fname)
        #    logging.info("loaded model for %s", lang)
    def getDocumentation(self):
        return "Annotation server for VaLID system"
    def annotate(self, communication):
        text = communication.text
        scores = self.classifier.classify(text)
        print scores
        augf = AnalyticUUIDGeneratorFactory(communication)
        aug = augf.create()
        lid = LanguageIdentification(uuid=aug.next(),
                                     languageToProbabilityMap=scores,
                                     metadata=AnnotationMetadata(tool="valid", timestamp=int(time.time()), kBest=1),
        )
        communication.lidList.append(lid)
        return communication
    
if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", dest="port", type=int, default=9090)
    parser.add_argument("-m", "--model_path", dest="model_path")
    options = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    
    handler = CommunicationHandler(options.model_path)
    processor = Annotator.Processor(handler)
    transport = TSocket.TServerSocket(port=options.port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TCompactProtocol.TCompactProtocolFactory()

    server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
    logging.info('Starting the server...')
    server.serve()
