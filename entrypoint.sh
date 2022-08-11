#!/bin/bash

# Browse the entrypoint files
# (It is supposed that the entrypoint files are called 'entrypoint.sh' and
# located at the root of each subfolder)
for subdirectory in ./*; do
  if [ -d "${subdirectory}" ]; then
    entrypoint_file="${subdirectory}"/entrypoint.sh
    if [ -f "$entrypoint_file" ]; then
      # If any, launch the entrypoint
      bash $entrypoint_file
    fi
  fi
done

# Run the Docker command
exec "$@"
