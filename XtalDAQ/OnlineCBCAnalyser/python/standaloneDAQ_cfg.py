import FWCore.ParameterSet.python.Config as cms 

# process declaration
process = cms.Process("HLT") 

process.TFileService = cms.Service("TFileService",
	fileName = cms.string("/home/xtaldaq/testHistograms.root")
)

process.load("FWCore.MessageLogger.python.MessageLogger_cfi") 
process.MessageLogger = cms.Service("MessageLogger", 
	destinations = cms.untracked.vstring('cout','log4cplus'), 
	cout = cms.untracked.PSet(threshold = cms.untracked.string('WARNING')), 
	log4cplus = cms.untracked.PSet(
		INFO = cms.untracked.PSet( reportEvery = cms.untracked.int32(1) ),
		threshold = cms.untracked.string('WARNING')
	) 
)


process.source = cms.Source("DaqSource",
	readerPluginName = cms.untracked.string('FUShmReader'),
	evtsPerLS = cms.untracked.uint32(1000000)
)

#process.load("MarksAnalysers.CBCAnalyser.AnalyseCBCOutput_cfi")
process.AnalyseCBCOutput = cms.EDAnalyzer("AnalyseCBCOutput",
	trimFilename = cms.string("/tmp/i2CFileToSendToBoard.txt"),
	outputFilename = cms.string("/home/xtaldaq/output.log")
)
process.path1 = cms.Path(process.AnalyseCBCOutput)


process.consumer = cms.OutputModule("ShmStreamConsumer",
	compression_level = cms.untracked.int32(1),
	use_compression = cms.untracked.bool(True)
	)

process.outpath = cms.EndPath( process.consumer )

