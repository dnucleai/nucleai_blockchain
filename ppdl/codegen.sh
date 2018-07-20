cd common
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. *.proto
cd ..

cp common/* master/
cp common/* worker/
