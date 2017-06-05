#!/bin/bash
python ../../code/convert2yang.py \
	--config ../../config/yangtool.conf \
	--section default \
	--verbose \
	$*
