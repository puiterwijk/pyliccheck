#!/bin/sh
failed=false
for env in python2 python3
do
	if command -v ${env}
	then
		echo "Running for ${env}"
		if ${env} ./check.py
		then
			echo "Check passed"
		else
			echo "CHECK FAILED"
			failed=true
		fi
	else
		echo "No ${env}"
	fi
done

if $failed
then
	echo "Some failures occured"
	exit 1
fi
