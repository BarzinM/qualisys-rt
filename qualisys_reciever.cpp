#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <stdio.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>  //write
#include <iostream>
#include <bitset>

int main(int argc,char **argv)
{
    int sockfd;
    // char sendline[100];
    char recvline[4];
    // std::bitset<8>binarya(a);
    struct sockaddr_in servaddr;
    // float position_value;
 
    sockfd=socket(AF_INET,SOCK_STREAM,0);
    // bzero(&servaddr,sizeof servaddr);
 
    servaddr.sin_family=AF_INET;
    servaddr.sin_port=htons(1895);
 
    inet_pton(AF_INET,"192.168.0.25",&(servaddr.sin_addr));
 
    connect(sockfd,(struct sockaddr *)&servaddr,sizeof(servaddr));

    // unsigned char checker;
 
    while(1)
    {
        read(sockfd,recvline,1);
        // checker = (unsigned char)*recvline;
        if((int)recvline[0] == 2){
            std::cout<<"Hahahaha"<<std::endl;
            read(sockfd,recvline,4);
            std::cout<<*(float*)recvline<<std::endl;
            read(sockfd,recvline,4);
            std::cout<<*(float*)recvline<<std::endl;
            read(sockfd,recvline,4);
            std::cout<<*(float*)recvline<<std::endl;
        }
    }
 
}