cmake_minimum_required(VERSION 3.16)
project(AdvancedNetworkReliabilityAnalyzer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(network_reliability
    src/main.cpp
    src/graph.cpp
    src/topology.cpp
    src/reliability.cpp
    src/simulation.cpp
)

if(MSVC)
    target_compile_options(network_reliability PRIVATE /W4 /permissive-)
else()
    target_compile_options(network_reliability PRIVATE -Wall -Wextra -Wpedantic)
endif()
