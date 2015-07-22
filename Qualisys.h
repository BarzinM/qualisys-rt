// UM7 classes header
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <stdio.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>  //write
#include <iostream>
#include <bitset>
#include <stdlib.h>

class Body{
public:
    float position_x, position_y, position_z;
    float roll, pitch, yaw;

    void print();
};

void Body::print(){
    printf("%f, %f, %f, %f, %f, %f\n",position_x, position_y, position_z, roll, pitch, yaw);
}

class PositionReciever{
private:
public:
    Body object;
    int socket_handle;
    char recieved_value[4];

    // PositionReciever();
    // ~PositionReciever();
    void connect_to_server();
    Body getStatus();
};

// PositionReciever::PositionReciever(){};
// PositionReciever::~PositionReciever(){};

void PositionReciever::connect_to_server(){
    // int socket_handle;
    // char sendline[100];
    // char recieved_value[4];
    // std::bitset<8>binarya(a);
    struct sockaddr_in servaddr;
    // float position_value;

    socket_handle=socket(AF_INET,SOCK_STREAM,0);
    int iSetOption = 1;
    // setsockopt(socket_handle, SOL_SOCKET, SO_REUSEADDR, (char*)&iSetOption,sizeof(iSetOption));
    // bzero(&servaddr,sizeof servaddr);

    servaddr.sin_family=AF_INET;
    servaddr.sin_port=htons(1895);

    inet_pton(AF_INET,"192.168.0.25",&(servaddr.sin_addr));

    int connection_status = connect(socket_handle,(struct sockaddr *)&servaddr,sizeof(servaddr));\
    // std::cout<<connection_status<<std::endl;
    if (connection_status!=0){
        // std::cout<<"something else"<<std::endl;
        printf("Connection Error!!!\n");
        exit(EXIT_FAILURE);
    }
    else{
        printf("Connection Established!\n");
    }
}

Body PositionReciever::getStatus(){
        read(socket_handle,recieved_value,1);
        if((int)recieved_value[0] == 2){
            read(socket_handle,recieved_value,4);
            object.position_x = *(float*)recieved_value;
            read(socket_handle,recieved_value,4);
            object.position_y = *(float*)recieved_value;
            read(socket_handle,recieved_value,4);
            object.position_z = *(float*)recieved_value;
            read(socket_handle,recieved_value,4);
            object.roll = *(float*)recieved_value;
            read(socket_handle,recieved_value,4);
            object.pitch = *(float*)recieved_value;
            read(socket_handle,recieved_value,4);
            object.yaw = *(float*)recieved_value;
            return object;
        }
        else{
            printf("packet matching warning!!!\n");
        }
}