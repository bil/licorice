#include <stdint.h>
#include <stdio.h>
#include <stdbool.h>

#ifndef _NETWORK_UTILITIES_
#define _NETWORK_UTILITIES_

//channNum is the number of channel you want to operate on. Offset is the number of bytes (positive) you want to
//movement to the left, and curPtr is from where you want to move.  Make sure curPtr is a pointer to valid data 
//(i.e. is not pointing to end of chunk)
uint8_t* calcLeftOffsetInBlock(uint8_t channNum, size_t offset, uint8_t* curPtr);

uint8_t* calcRightOffsetInBlock(uint8_t channNum, size_t offset, uint8_t* curPtr);

void init_pointers(bool network);

#endif
