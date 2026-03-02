"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { ChevronsUpDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { GeoCountry } from "@/lib/api";

interface PhoneInputProps {
  countries: GeoCountry[];
  dialCode: string;
  number: string;
  onDialCodeChange: (dialCode: string) => void;
  onNumberChange: (number: string) => void;
  required?: boolean;
}

export function PhoneInput({
  countries,
  dialCode,
  number,
  onDialCodeChange,
  onNumberChange,
  required = false,
}: PhoneInputProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const filtered = search
    ? countries.filter(
        (c) =>
          c.name.toLowerCase().includes(search.toLowerCase()) ||
          (c.phone_code ?? "").includes(search),
      )
    : countries;

  const selected = countries.find((c) => c.phone_code === dialCode);

  return (
    <div className="flex">
      {/* Dial-code selector */}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="shrink-0 rounded-r-none border-r-0 px-3 font-normal"
          >
            <span className="mr-1">{selected?.emoji ?? "🌐"}</span>
            <span className="text-muted-foreground">
              {dialCode ? `+${dialCode}` : "Code"}
            </span>
            <ChevronsUpDown className="ml-1 h-3 w-3 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-72 p-0">
          <Command shouldFilter={false}>
            <CommandInput
              placeholder="Search country..."
              value={search}
              onValueChange={setSearch}
            />
            <CommandList>
              <CommandEmpty>No results found.</CommandEmpty>
              <CommandGroup>
                {filtered.map((c) => (
                  <CommandItem
                    key={c.iso2}
                    value={c.iso2}
                    onSelect={() => {
                      onDialCodeChange(c.phone_code ?? "");
                      setSearch("");
                      setOpen(false);
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4 shrink-0",
                        dialCode === c.phone_code ? "opacity-100" : "opacity-0",
                      )}
                    />
                    <span className="mr-2">{c.emoji}</span>
                    <span className="flex-1 truncate">{c.name}</span>
                    <span className="ml-2 text-muted-foreground text-xs">
                      +{c.phone_code}
                    </span>
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      {/* Number input */}
      <Input
        id="phone"
        type="tel"
        value={number}
        onChange={(e) => onNumberChange(e.target.value)}
        required={required}
        placeholder="555 000 0000"
        className="rounded-l-none"
      />
    </div>
  );
}
