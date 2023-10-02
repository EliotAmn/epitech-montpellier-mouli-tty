#!/usr/bin/bash

touch ~/.moulitoken

AUTH_TOKEN=$(cat ~/.moulitoken)


login() {
	data_row='{"username": "'
	data_row+=$1
	data_row+='", "password": "'
	data_row+=$2
	data_row+='"}'
	REQ_RESULT=$(curl -s --location 'https://tekme.eu/api/auth/login/bocal'	--header 'Content-Type: application/json' --data-raw "$data_row")
	AUTH_TOKEN=$(echo "$REQ_RESULT" | jq ".token")
	AUTH_TOKEN=$(echo $AUTH_TOKEN | tr -d '"')
	echo $AUTH_TOKEN > ~/.moulitoken
}



mouli_data() {
	req_header='Authorization:'
	req_header+=$AUTH_TOKEN
	req_header+=''
	#echo $req_header
	mdj=$(curl -s --location 'https://tekme.eu/api/profile/moulinettes' --header $req_header)
}


if [[ "$1" == "login" ]]
then
	echo "Entrez votre email Epitech: "
	read username
	echo "Entrez votre mot de passe Epitech: "
	read -s password
	login $username $password
fi



mouli_data

mdj=$(echo "$mdj" | jq ".jobs[0]" | tr -d '\n')

M_ID=$(echo "$mdj" | jq ".id" | tr -d '"')
M_PROJ=$(echo "$mdj" | jq ".project" | tr -d '"')
M_USER=$(echo "$mdj" | jq ".login" | tr -d '"')
M_DATE=$(echo "$mdj" | jq ".trace.date" | tr -d '"')
M_DATE=$(TZ=UTC-2 date -d "$M_DATE" +'%F %T %Z')

M_ERR_MAJOR=$(echo "$mdj" | jq ".externalItems[0].value" | tr -d '"')
M_ERR_MINOR=$(echo "$mdj" | jq ".externalItems[1].value" | tr -d '"')
M_ERR_INFO=$(echo "$mdj" | jq ".externalItems[2].value" | tr -d '"')



get_trace() {
	req_header='Authorization:'
        req_header+=$AUTH_TOKEN
        req_header+=''
        mtrace=$(curl -s --location "https://tekme.eu/api/profile/moulinettes/$M_ID/trace" --header $req_header)
	mtrace=$(echo $mtrace | jq ".trace_pool")
}


gen_test() {
    data=$1
    name=$(echo $data | jq -r ".name")
    passed=$(echo $data | jq ".passed")
    crashed=$(echo $data | jq ".crashed")
    comment=$(echo $data | jq ".comment")
    end_text=""


    if [[ $passed == "false" ]]
    then
        status="\e[31mFAILED\e[39m"
   	end_text="($comment)"
    fi

    if [[ $passed == "true" ]]
    then
        status="\e[32mPASSED\e[39m"
    fi

    if [[ $crashed == "true" ]]
    then
        status="\e[101mCRASHED\e[39m"
	end_text="($comment)"
    fi
    echo -e "--> $name $status $end_text"

}




echo "================= EPITECH MOULI ==================="
echo "                   $M_PROJ"
echo "                  $M_USER"
echo "               $M_DATE"
echo "==================================================="
echo "Issues overview :"
echo ""
echo -e "\e[31mMAJORS: $M_ERR_MAJOR"
echo -e "\e[93mMINORS $M_ERR_MINOR"
echo -e "\e[34mINFO: $M_ERR_INFO"
echo -e "\e[39m====== SKILS ======="
#echo $mdj
echo "$mdj" | jq -c '.trace.skills[]' | while IFS=$"\n" read -r c; do
    name=$(echo "$c" | jq -r '.name')
    echo -e "\e[96m"
    echo -e $name "\e[39m"
    echo "$c" | jq -c '.tests[]' | while IFS=$"\n" read -r rr; do
        gen_test "$rr"
	testname=$(echo "$rr" | jq -r ".name")
	comment=$(echo "$rr" | jq -r ".comment")
    done
done


if [[ "$1" == "trace" ]]
then
    get_trace
    echo "=========== TRACE ==========="
    echo ""
    decoded_text=$(echo "$mtrace" | jq -r '.')
    last_success=$(echo "$decoded_text" | awk -v RS=": SUCCESS" 'END{print $0}')
    printf "%s\n" "$last_success"
fi
