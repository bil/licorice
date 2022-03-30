#include "networkUtilities.h"
#include "constants.h"
#include <stdlib.h>
#include <stdbool.h>
#include <assert.h>

extern uint8_t *pChannInits[NUM_CHANNELS];
extern uint8_t *pChannEnds[NUM_CHANNELS];
extern int channInitPmemIndex[NUM_CHANNELS];
extern uint8_t *gpPmems[NUM_GRP_SEGS];
extern uint8_t *gpPmemEnds[NUM_GRP_SEGS];
extern uint8_t *pTimestamp;
extern uint8_t *pTimestampInit;
extern uint8_t *pTimestampEnd;
extern uint8_t *pChanns[NUM_CHANNELS];

//channNum is the number of channel you want to operate on. Offset is the number of bytes (positive) you want to
//movement to the left, and curPtr is from where you want to move.  Make sure curPtr is a pointer to valid data 
//(i.e. is not pointing to end of chunk)
uint8_t* calcLeftOffsetInBlock(uint8_t channNum, size_t offset, uint8_t* curPtr) {
	//offset = offset * multiplier;
	//pointer to end of block
	uint8_t* endPtr = pChannEnds[channNum-1];
	//pointer to start of block
	uint8_t* startPtr = pChannInits[channNum-1];
	//pointer to end of chunk associated with current block
	uint8_t* chunkInitEnd = gpPmemEnds[channInitPmemIndex[channNum-1]];
	//check for illegal values
	assert(curPtr != chunkInitEnd && curPtr != endPtr);
	//start of next block.  Only useful if we span multiple blocks so used as boolean to check if multiple blocks are spanned
	uint8_t* chunkNextStart = NULL;
	//firstHalf is irrelevent if chunkNextStart remains NULL, so it does not need to be intialized
	bool firstHalf = NULL;
	// uint8_t* retVal;
	//don't want to do expensive instruciton for no reason, so use if statement and hope branch
	//prediction works
	if (offset > CHANNEL_BLOCKSIZE) {
		offset %= CHANNEL_BLOCKSIZE;
	}
	//spans multiple blocks
	if((chunkInitEnd - startPtr) < CHANNEL_BLOCKSIZE) {
		chunkNextStart = gpPmems[channInitPmemIndex[channNum-1] + 1];
		firstHalf = ((curPtr < chunkInitEnd) && (curPtr >= startPtr));
	}
	while(1) {
		if(chunkNextStart) {
			if(firstHalf) {
				if((curPtr - startPtr) >= offset) {
					return curPtr - offset;
				}
				else {
					offset = offset - (curPtr - startPtr);
					//this is OK since the associated if will catch the case where the offset is zero, so this
					//will never return an illegal pointer
					curPtr = endPtr;
					firstHalf = false;
				}
			}
			else {
				if((curPtr - chunkNextStart) >= offset) {
					return curPtr - offset;
				}
				else {
					offset = offset - (curPtr - chunkNextStart);
					//this is OK since the associated if will catch the case where the offset is zero, so this
					//will never return an illegal pointer
					curPtr = chunkInitEnd;
					firstHalf = true;
				}
			}
		}
		else {
			if((curPtr - startPtr) >= offset) {
				return curPtr - offset;
			}
			else {
				offset = offset - (curPtr - startPtr);
				curPtr = endPtr;
			}
		}
	}
	return NULL;
}

uint8_t* calcRightOffsetInBlock(uint8_t channNum, size_t offset, uint8_t* curPtr) {
	//pointer to end of block
	uint8_t* endPtr = pChannEnds[channNum-1];
	//pointer to start of block
	uint8_t* startPtr = pChannInits[channNum-1];
	//pointer to end of chunk associated with current block
	uint8_t* chunkInitEnd = gpPmemEnds[channInitPmemIndex[channNum-1]];
	//check for illegal values
	assert(curPtr != chunkInitEnd && curPtr != endPtr);
	//start of next block.  Only useful if we span multiple blocks so used as boolean to check if multiple blocks are spanned
	uint8_t* chunkNextStart = NULL;
	//firstHalf is irrelevent if chunkNextStart remains NULL, so it does not need to be intialized
	bool firstHalf = NULL;
	//don't want to do expensive instruciton for no reason, so use if statement and hope branch
	//prediction works
	if (offset > CHANNEL_BLOCKSIZE) {
		offset %= CHANNEL_BLOCKSIZE;
	}

	//second try 
	//spans multiple blocks
	if((chunkInitEnd - startPtr) < CHANNEL_BLOCKSIZE) {
		chunkNextStart = gpPmems[channInitPmemIndex[channNum-1] + 1];
		firstHalf = ((curPtr < chunkInitEnd) && (curPtr >= startPtr));
	}
	while(1) {
		if(chunkNextStart) {
			if(firstHalf) {
				if((chunkInitEnd - curPtr) > offset) {
					return curPtr + offset;
				}
				else {
					offset = offset - (chunkInitEnd - curPtr);
					curPtr = chunkNextStart;
					firstHalf = false;
				}
			}
			else {
				if((endPtr - curPtr) > offset) {
					return curPtr + offset;
				}
				else {
					offset = offset - (endPtr - curPtr);
					curPtr = startPtr;
					firstHalf = true;
				}
			}
		}
		else {
			if((endPtr - curPtr) > offset) {
				return curPtr + offset;
			}
			else {
				offset = offset - (endPtr - curPtr);
				curPtr = startPtr;
			}
		}
	}
	return NULL;
	//end second try
}

void init_pointers(bool network) {
  // initialize pTimestamp and pChanns pointers
  pTimestampInit = gpPmems[0];
  if (network) {
  	pTimestamp = pTimestampInit;
  }
  pTimestampEnd = pTimestampInit + 2 * CHANNEL_BLOCKSIZE;
  unsigned int offset = 0;
  unsigned int iBlock = 2;
  for (int i = 0, j = 0; i < NUM_CHANNELS; i++) {
    if (CHANNEL_BLOCKSIZE * iBlock + offset >= BYTES_IN_GB) {
      j++;
      offset = (CHANNEL_BLOCKSIZE * iBlock + offset) - BYTES_IN_GB;
      iBlock = 0;
    }
    channInitPmemIndex[i] = j;
  	pChannInits[i] = gpPmems[j] + CHANNEL_BLOCKSIZE * iBlock + offset;	
    if (network) {
    	pChanns[i] = pChannInits[i];
    }
    iBlock++;
  }  

  bool diffStartEnd;
  for (int i = 0; i < NUM_CHANNELS - 1; i++) {
    diffStartEnd = false;
    int j;
    for (j = 0; j < NUM_GRP_SEGS; j++) {
      if (pChannInits[i] == gpPmems[j]) {
        diffStartEnd = true;
        break;
      } 
    }
    if (diffStartEnd) {
      pChannEnds[i] = gpPmemEnds[j - 1];
    }
    else {
      pChannEnds[i] = pChannInits[i + 1]; 
    }
  }
  // set the last pChannEnds to the last pChannsInits plus block size if the last channel is completely within one block
  if (NUM_GRP_SEGS == 1 || channInitPmemIndex[NUM_CHANNELS - 1] == NUM_GRP_SEGS - 1) {
    pChannEnds[NUM_CHANNELS - 1] = pChannInits[NUM_CHANNELS - 1] + CHANNEL_BLOCKSIZE;
  }
  // otherwise set the last pChannEnds to the last chunk start pointer plus the offset from the last chunk
  else {
    //This line doesn't work if there is only one grp seg
    pChannEnds[NUM_CHANNELS - 1] = gpPmems[NUM_GRP_SEGS - 1] + (pChannInits[NUM_CHANNELS - 1] + CHANNEL_BLOCKSIZE - gpPmemEnds[NUM_GRP_SEGS - 2]);
  }
}