OBJECTS = LKmain.o Activate.o AdjustCandidateSet.o Ascent.o\
 	  Backtrack2OptMove.o Backtrack3OptMove.o\
	  Backtrack4OptMove.o Backtrack5OptMove.o\
 	  Best2OptMove.o Best3OptMove.o Best4OptMove.o Best5OptMove.o\
          Between.o Between_SL.o BridgeGain.o\
          C.o ChooseInitialTour.o Connect.o CreateCandidateSet.o\
          Distance.o eprintf.o Exclude.o Excludable.o\
          FindTour.o Flip.o Flip_SL.o Forbidden.o FreeStructures.o\
	  Gain23.o GenerateCandidates.o GetTime.o Hashing.o Heap.o\
          LinKernighan.o Make2OptMove.o Make3OptMove.o\
          Make4OptMove.o Make5OptMove.o Minimum1TreeCost.o\
          MinimumSpanningTree.o NormalizeNodeList.o PrintBestTour.o\
	  PrintParameters.o ReadLine.o ReadParameters.o ReadProblem.o\
          RecordBestTour.o RecordBetterTour.o RemoveFirstActive.o\
          ResetCandidateSet.o RestoreTour.o StoreTour.o

CFLAGS= -O3

CC = cc

all: ${OBJECTS}
	${CC} ${CFLAGS} ${OBJECTS} -o ../LKH.UNIX -lm

clean:
	/bin/rm -f ${OBJECTS} ../LKH.UNIX

