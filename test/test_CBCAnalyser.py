# Configuration file to run my analyser on CBC1 data. Only tested with simulated data since
# I can't currently get the glib to trigger without a TTC setup.
# Mark Grimes (mark.grimes@bristol.ac.uk)
import FWCore.ParameterSet.Config as cms

process = cms.Process('CBCTest')

# import of standard configurations
process.load('Configuration.StandardSequences.Services_cff')
process.load('FWCore.MessageService.MessageLogger_cfi')

#process.load('XtalDAQ.Configuration.python.StandardSetup_cfi')
#process.load('XtalDAQ.SiStripESProducers.python.SiStripFedCablingXtalESSource_cfi')
#process.load('XtalDAQ.SiStripESProducers.python.SiStripXtalPedestalsESSource_cfi')
#process.load('XtalDAQ.SiStripESProducers.python.SiStripXtalNoisesESSource_cfi')
#process.load('CalibTracker.SiStripESProducers.python.fake.SiStripQualityFakeESSource_cfi')
#process.load('XtalDAQ.SiStripESProducers.python.SiStripXtalApvGainsESSource_cfi')

#process.siStripFedCabling = cms.ESSource("SiStripFedCablingXtalESSource",
#	FedIdsFile       = cms.FileInPath('XtalDAQ/SiStripCommon/data/SiStripFedIdList.dat'),
#	DetIdsFile       = cms.FileInPath('XtalDAQ/SiStripCommon/data/SiStripDetInfo.dat'),
#	ApvFedMapFile    = cms.FileInPath('XtalDAQ/SiStripCommon/data/SiStripApvFedMapInfo.dat')
#	)

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(-1)
)

# Input source
process.source = cms.Source("NewEventStreamFileReader",
    fileNames = cms.untracked.vstring(
    	#'file:/home/xtaldaq/data/closed/outputFrom_piste.txt_.dat',
    	#'file:/home/xtaldaq/data/closed/outputFrom_marksTest.txt_.dat'
    	#'file:/tmp/memDump.dat',
    	#'file:/home/xtaldaq/data/closed/outputFrom_pistes.txt_.dat',
    	'file:/home/xtaldaq/data/closed/USC.00000001.0001.A.storageManager.00.0000.dat'
    	)
)

process.options = cms.untracked.PSet(

)

# Production Info
process.configurationMetadata = cms.untracked.PSet(
    version = cms.untracked.string('$Revision: 1.2 $'),
    annotation = cms.untracked.string('test nevts:1'),
    name = cms.untracked.string('PyReleaseValidation')
)

# Output definition

process.RECOSIMoutput = cms.OutputModule("PoolOutputModule",
    splitLevel = cms.untracked.int32(0),
    eventAutoFlushCompressedSize = cms.untracked.int32(5242880),
    outputCommands = cms.untracked.vstring("keep *"),
    fileName = cms.untracked.string('test_DIGI.root'),
    dataset = cms.untracked.PSet(
        filterName = cms.untracked.string(''),
        dataTier = cms.untracked.string('')
    )
)

process.analyse = cms.EDAnalyzer("AnalyseCBCOutput")

# Path and EndPath definitions
process.analyse_step = cms.Path(process.analyse)
process.RECOSIMoutput_step = cms.EndPath(process.RECOSIMoutput)


# Schedule definition
process.schedule = cms.Schedule(process.analyse_step,process.RECOSIMoutput_step)

