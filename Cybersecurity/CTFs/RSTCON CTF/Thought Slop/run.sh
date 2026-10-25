#!/bin/sh
socat -T120 tcp-l:8888,reuseaddr,fork,max-children=4 EXEC:"./thoughtful",pty,stderr