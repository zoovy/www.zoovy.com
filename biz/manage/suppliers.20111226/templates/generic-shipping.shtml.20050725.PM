<!-- REPORT_TAB -->

<center>
<table width=80%><tr><Td>

<form method="POST" action="index.cgi">
<input type="hidden" name="ACTION" value="SAVE-GENERIC-SHIPPING">
<input type="hidden" name="CODE" value="<!-- CODE -->">
<table>
	<tr>
		<td>Supplier Code: <!-- CODE --></td>
	</tr>
	<tr>
		<td><!-- RESULT --></td>
	</tr>
</table>
<br>
<table>

	<tr>
		<td colspan='2'><input type="checkbox" name="GEN_SHIPMETHODS_1" <!-- GEN_SHIPMETHODS_1 -->> <b>Enable Fixed Price Shipping</b></td>
	</tr>
	<tr>
		<td width='30'>&nbsp;&nbsp;&nbsp;</td>
		<td>
			<i>If fixed shipping is enabled, you can set a shipping cost per product.</i>
		</td>
	</tr>
	
	<tr>
		<td colspan='2'><input type="checkbox" name="GEN_SHIPMETHODS_2" <!-- GEN_SHIPMETHODS_2 -->> <b>Enable Zone Based Shipping</b></td>
	</tr>
	<tr>
		<td width='30'>&nbsp;&nbsp;&nbsp;</td>
		<td>	
			<table>
				<tr>
					<td width='35%'>Origin Zip Code:</td>
					<td><input type="textbox" size="5" name="GEN_SHIPORIGZIP" value="<!-- GEN_SHIPORIGZIP -->"></td>
				</tr>
				<tr>
					<td width='35%'>Origin State:</td>
					<td><input type="textbox" size="2" maxsize="2" name="GEN_SHIPORIGSTATE" value="<!-- GEN_SHIPORIGSTATE -->"></td>
				</tr>
				<tr>
					<td width='35%'>Origin Account #:</td>
					<td><input type="textbox" size="10" name="GEN_SHIPACCOUNT" value="<!-- GEN_SHIPACCOUNT -->"></td>
				</tr>
				<tr>
					<td width='35%'>Provider:</td>
					<td>
						<input type="radio" name="GEN_SHIPPROVIDER" value="UPS" <!-- GEN_SHIPPROVIDER_UPS --> > UPS 
						<input type="radio" name="GEN_SHIPPROVIDER" value="FEDEX" <!-- GEN_SHIPPROVIDER_FEDEX --> > FEDEX 
					</td>
				</tr>
				<tr>
					<td colspan='2'>
					<input type="checkbox" name="GEN_SHIPOPTIONS_1" <!-- GEN_SHIPOPTIONS_1 --> > Quote each package as its own shipment<br>
					<i>HINT: enable this when the items being shipped in individual boxes.</i>
					</td>
				</tr>
			</table>			
		</td>
	</tr>

	<tr>
		<td colspan='2'><input type="checkbox" name="GEN_SHIPMETHODS_32" <!-- GEN_SHIPMETHODS_32 -->> <b>Handling Fees</b></td>
	</tr>
	<tr>
		<td width='30'>&nbsp;&nbsp;&nbsp;</td>
		<td>
			<table>
				<tr>
					<td>Per Order</td>
					<td>$<input type="textbox" name="GEN_HNDPERORDER" value="<!-- GEN_HNDPERORDER -->" size="5"></td>
				</tr>
				<tr>
					<td>Per Item</td>
					<td>$<input type="textbox" name="GEN_HNDPERITEM" value="<!-- GEN_HNDPERITEM -->" size="5"></td>
				</tr>
				<tr>
					<td>Per Unique Item</td>
					<td>$<input type="textbox" name="GEN_HNDPERUNIITEM" value="<!-- GEN_HNDPERUNIITEM -->" size="5" ></td>
				</tr>
			</table>
		</td>
	</tr>
</table>

<center>
<table>
   <tr>
      <td><input type="image" src="/images/bizbuttons/save.gif"></td>
      <td><a href="index.cgi?ACTION=GENERIC-EDIT&CODE=<!-- CODE -->">
      <img border=0 src="/images/bizbuttons/exit.gif"></a></td>
   </tr>
</table>
</center>
		
</form>

</td></tr></table>
</center>
<!-- FOOTER -->

