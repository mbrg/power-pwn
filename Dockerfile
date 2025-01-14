FROM mcr.microsoft.com/devcontainers/python:1-3.8

# Create a new user with a home directory
RUN useradd -ms /bin/bash powerpwn

# Create a sudoers file to allow limited sudo permissions for the user
RUN echo "powerpwn ALL=(ALL) NOPASSWD: /usr/bin/apt-get, /usr/bin/apt, /usr/bin/mv, /usr/bin/chmod" > /etc/sudoers.d/powerpwn \
    && chmod 440 /etc/sudoers.d/powerpwn

USER powerpwn
WORKDIR /home/powerpwn/power-pwn

COPY --chown=powerpwn:powerpwn . .

RUN chmod +x .devcontainer/setup.sh && ./.devcontainer/setup.sh
RUN chmod +x start-container-webserver.sh

RUN echo "/home/powerpwn/power-pwn/start-container-webserver.sh> /dev/null 2>&1 &" >> /home/powerpwn/.bashrc
RUN echo "clear" >> /home/powerpwn/.bashrc
RUN echo "echo Please visit http://localhost:8765 in your browser to access result files" >> /home/powerpwn/.bashrc

ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV PYTHONPATH=/home/powerpwn/power-pwn/src/

USER root
RUN rm /etc/sudoers.d/powerpwn

USER powerpwn