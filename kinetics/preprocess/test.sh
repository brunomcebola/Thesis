#!/bin/bash

input_dir="input"
output_dir="output"
fps=25

for input_file in "$input_dir"/*.mp4; do
    filename=$(basename "$input_file")
    output_file="$output_dir/$filename"
    echo -n "Processing $filename: "

    # Start processing and capture the output
    ffmpeg -i "$input_file" -filter:v "fps=$fps" "$output_file" -progress - 2>&1 | while IFS= read -r line; do
        # Extract duration and time data
        if [[ $line =~ ^duration= ]]; then
            duration=$(echo "$line" | cut -d= -f2)
            duration_ms=$(echo "$duration * 1000" | bc)
        elif [[ $line =~ ^out_time_ms= ]]; then
            out_time_ms=$(echo "$line" | cut -d= -f2)
            percentage=$(echo "scale=2; ($out_time_ms / $duration_ms) * 100" | bc)
            printf "\rProcessing $filename: %.2f%%" "$percentage"
        fi
    done

    echo -e "\nDone."
done