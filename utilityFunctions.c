#include "utilityFunctions.h"
#include "constants.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

extern uint8_t *pChanns[NUM_CHANNELS];
extern uint8_t *pChannInits[NUM_CHANNELS];
extern uint8_t *pChannEnds[NUM_CHANNELS];
extern int channInitPmemIndex[NUM_CHANNELS];
extern uint8_t *gpPmems[NUM_GRP_SEGS];
extern uint8_t *gpPmemEnds[NUM_GRP_SEGS];
//offset in bytes
uint8_t* calcOffsetInBlock(uint8_t blockNum, int offset, uint8_t* curPtr) {
	//offset = offset * multiplier;
	//uint8_t* curPtr = pChanns[blockNum];
	uint8_t* endPtr = pChannEnds[blockNum];
	uint8_t* startPtr = pChannInits[blockNum];
	uint8_t* chunkInitEnd = gpPmemEnds[blockNum];
	//don't want to do expensive instruciton for no reason, so use if statement and hope branch
	//prediction works
	if (offset > CHANNEL_BLOCKSIZE) {
		offset %= CHANNEL_BLOCKSIZE;
	}
	int absOffset = abs(offset);
	if (absOffset > CHANNEL_BLOCKSIZE/2) {
		offset = (offset < 0) ? (CHANNEL_BLOCKSIZE + offset) : -(CHANNEL_BLOCKSIZE - offset);
		absOffset = abs(offset);
	}
	uint8_t* retVal = curPtr + offset;
	//logic to deal with block spanning two chunks
	if(chunkInitEnd - startPtr < CHANNEL_BLOCKSIZE) {
		uint8_t* nextChunkStart = gpPmems[channInitPmemIndex[blockNum + 1]];
		//curPtr in first half of block
		if(curPtr < chunkInitEnd && curPtr >= startPtr) {
			if(offset <= 0) {
				int differenceNeg = curPtr - startPtr;
				if(absOffset  > differenceNeg) {
					return  endPtr + (offset + differenceNeg);
				}
				else {
					retVal = curPtr + offset;
				}
			}
			else {
				int differencePos = chunkInitEnd - curPtr;
				if(differencePos <= absOffset) {
					return nextChunkStart + (offset - differencePos);
				}
				else {
					retVal = curPtr + offset;
				}
			}
		}
		//curPtr in second half of block
		else if (curPtr >= nextChunkStart && curPtr < endPtr) {
			if(offset <= 0) {
				int differenceNeg = curPtr - nextChunkStart;
				if(absOffset  > differenceNeg) {
					return  chunkInitEnd + (offset + differenceNeg);
				}
				else {
					retVal = curPtr + offset;
				}
			}
			else {
				int differencePos = endPtr - curPtr;
				if(differencePos <= absOffset) {
					return startPtr + (offset - differencePos);
				}
				else {
					retVal = curPtr + offset;
				}
			}
		}
		else {
			printf("offset calc error\n");
		}
	}
	//if add CHANNEL_BLOCKSIZE/2 to curPtr when half way through block, you get the endPtr, which isn't valid
	if (retVal == endPtr) {
		retVal = startPtr;
	}
	return retVal;
}