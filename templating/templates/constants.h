
#ifndef _CONSTANTS_
#define _CONSTANTS_ 
/************************************
* Basic user configurable constants *
*************************************/
/* 
* Non-zero if using line-level rather than cerebus input
*/
#define LINE 0
/*
* The offset from which to run the child processes, zero-indexed. Usually 
* the first (CPU 0) is for the parent timer process it self, the second
* is for Redis, the third is the network process (CPU 2), and the last is
* for the logger process (CPU 3). So, this should be a minimum of 4.
*/
#define CPU_OFFSET 4
/*
* The processor number on which to run the networking process, which is receiving
* packets from the Cerberus system.
*/
#define NETWORK_CPU 2
/*
* The processor number on which to run the data logging process
*/
#define LOGGER_CPU 3
/*
* The maximum number of child processes the timer process should have, excluding the network
* process. To specify the number of children and which executables are run, use runOrder.csv
*/
#define MAX_NUM_CHILDREN 3
/*
* The maximum number of rounds of child processes that are run. When a round finishes, the next 
* round is run and each previous round must be completely finished before the subsequent round
* is started. This option can technically be arbitrarily high, but there is a small static overhead
* for each round, so a lower number of rounds is generally better
*/
#define MAX_NUM_ROUNDS 3
/*
* The number of Cerebus channels that data is being read in on.
*/
#define NUM_CHANNELS (LINE ? 2 : 96)

/*
* The number of minutes of group data that is stored in shared memory at any given time.
*/
#define RECORDED_HISTORY 10

/*
* The sampling rate of the Cerebus system.
*/
#define SAMPLING_RATE 30000

/*
* CB packet type field associated with sampling rate.
*/
#define GP_TYPE 5
/*
* The number of samples sent in a spike packet per spike. Set on Cerberus host machine.
*/
#define SAMPLES_PER_SPIKE 48

/*
* Name of file for where data for the experiment should be stored.  48 character limit.
* DO NOT add .db to the end.
*/
#define DATALOGGER_FILENAME "experiment"

/*
* Table name for spike raster data.  Make sure this name complies with SQL syntax,
* since it is simply spliced into SQL command without any error checking.
*/
#define DATALOGGER_SPIKE_WAVEFORMS_TABLE_NAME "spike_waveforms_table"

/*
* Table name for continuous data.  Make sure this name complies with SQL syntax,
* since it is simply spliced into SQL command without any error checking.
*/
#define DATALOGGER_CONTINUOUS_DATA_TABLE_NAME "continuous_table"

/*
* Table name for key-value table.  Make sure this name complies with SQL syntax,
* since it is simply spliced into SQL command without any error checking.
*/
#define DATALOGGER_KEY_VALUE_TABLE_NAME "key_value_table"

/*
* Table name for units table.  Make sure this name complies with SQL syntax,
* since it is simply spliced into SQL command without any error checking.
*/
#define DATALOGGER_UNITS_TABLE_NAME "units_table"
/***************************************
* Advanced user configurable constants *
***************************************/

/*
* Max size of file pathname for child process execution.  The timer
* parent runs processes containing a max of MAX_PATH_LEN characters,
* including the null terminator.
*/
#define MAX_PATH_LEN 16

/*
* This is the number of milliseconds at the beginning of execution during which the 
* child processes do not run.
* Don't touch.
* Can be thought of as system latency. Using 50 for line since sound card has 20ms 
* buffer period.
*/
#define LATENCY (LINE ? 50 : 1)

/*
* The name of the network process.
*/
#define NETWORK_PROCNAME "./network"

/* 
* The name of the data logging process.
*/
#define LOGGER_PROCNAME "./logger"

/*******************
* Global constants *
********************/
/*
* NAMING CONVENTION:
* "chunk"- refers to any contiguous section of memory allocated with shm_open.
* "block"- refers to any subdivition of a chunk (e.g. a section of memory assocated with a channel).
* A block can span multiple chunks.
*/

//channel ID of group packet
#define GP_CHID 0

//Number of of microseconds for the timer interrupt (1 ms resolution)
#define USECREQ 1000

//Number of seconds for the timer interrupt
#define SECREQ 0

//Base address of parallel port output
#define PARA_PORT_BASE_ADDR 0x5000

//Process priority (1 (low) to 99 (high))
//Don't set to 99, or else process cannot be killed
#define PRIORITY 49

//Used to prefault the stack
#define MAX_SAFE_STACK (8*1024)

//Main shared memory pathname 
#define SMEM0_PATHNAME "/smem0"

//Spike packet shared memory pathname
#define SPK_SHM_NAME "/smem_spk"

//page size in bytes
#define PAGESIZE 4096

//Number of 4kB pages in a gB
#define NUM_PAGES_IN_GB 262144

//Number of bytes in a gigabyte
#define BYTES_IN_GB (1 << 30)

//Memory required for group packet data in THOUSANDS of bytes
//We add 2 to NUM_CHANNELS to store 4 byte timetamps (requires 2 channels worth of memory)
#define GRP_MEM_REQ ((NUM_CHANNELS + 2UL) * SAMPLING_RATE / 100 * RECORDED_HISTORY * 12) 

//Number of 1GB memory segments allocated for group packet data 
//hacky stuff here for integer overflow prevention
#define NUM_GRP_SEGS (((GRP_MEM_REQ * 125) % (BYTES_IN_GB/8)) ? (GRP_MEM_REQ * 125 / (BYTES_IN_GB / 8) + 1) : (GRP_MEM_REQ * 125 / (BYTES_IN_GB/8)))

//Number of bytes for one channel of data at the specified SAMPLING_RATE for RECORDED_HISTORY minutes 
#define CHANNEL_BLOCKSIZE (120UL * SAMPLING_RATE * RECORDED_HISTORY)

//Since exactly one bit is associated with a channel per ms, this tells us how many bytes we need per ms
#define NUM_BYTES_DIGITAL_RASTER_PER_MS ((NUM_CHANNELS % 8) ? ((NUM_CHANNELS / 8) + 1) : (NUM_CHANNELS / 8))

//first 2 is because we need two of these segments and the second is because data is a uint16_t.  The 4 
#define NUM_BYTES_FOR_SPIKE_FRAMES (2 * (2 * SAMPLES_PER_SPIKE + 4) * NUM_CHANNELS)

#define NUM_BYTES_DIGITAL_RASTER (NUM_BYTES_DIGITAL_RASTER_PER_MS * 60 *1000 * RECORDED_HISTORY)
//number of pages we need in a spike raster chunk
#define NUM_SPIKE_PAGES (((NUM_BYTES_FOR_SPIKE_FRAMES + NUM_BYTES_DIGITAL_RASTER) % PAGESIZE) ? ((NUM_BYTES_FOR_SPIKE_FRAMES + NUM_BYTES_DIGITAL_RASTER) / PAGESIZE + 1) : ((NUM_BYTES_FOR_SPIKE_FRAMES + NUM_BYTES_DIGITAL_RASTER) / PAGESIZE))

// number of samples in a millisecond 
#define NUM_SAMPLES_PER_MS (SAMPLING_RATE / 1000)

/*
* Header length of /smem0 in bytes
* Header layout:
* semaphore for network process [32 bytes] |
*     | current ms start offset [4 bytes] | current ms end offset (end of valid) [4 bytes] 
*     | start of valid data offset [4 bytes] | end of valid data offset [4 bytes] 
*     | offset to end of raster data [4 bytes]
*     | block wrapped? flag [1 byte] | empty [11 bytes]
*
*/
#define SMEM0_HEADER_LEN 64

//Number of bytes divided by 4 to current ms start in smem0 header
#define SMEM0_PTR_OFFSET 8

//Number of bytes divided by 4 to current ms start in smem0 header
#define SMEM0_MS_START_OFFSET (SMEM0_PTR_OFFSET + 0)

//Number of bytes divided by 4 to current ms end in smem0 header
#define SMEM0_MS_END_OFFSET (SMEM0_PTR_OFFSET + 1)

//Number of bytes divided by 4 to current ms end in smem0 header
#define SMEM0_DATA_START_OFFSET (SMEM0_PTR_OFFSET + 2)

//Number of bytes divided by 4 to current ms end in smem0 header
#define SMEM0_DATA_END_OFFSET (SMEM0_PTR_OFFSET + 3)

//Number of bytes divided by 4 to offset to end of raster data in smem0 header
#define SMEM0_RASTER_OFFSET (SMEM0_PTR_OFFSET + 4)

//Number of bytes divided by 4 to block wrapped? flag in smem0 header
#define SMEM0_WRAP_OFFSET (SMEM0_PTR_OFFSET + 5)

#define NUM_VALID_SAMPLES (RECORDED_HISTORY * 6 * SAMPLING_RATE - (2 * SAMPLING_RATE / 1000))

#define NUM_VALID_MS (RECORDED_HISTORY * 6000 - 2)

#endif